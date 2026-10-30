"""BGE-M3 embeddings and a persistent local Qdrant index for travel RAG."""

from __future__ import annotations

import hashlib
import json
import os
import re
import threading
import uuid
from pathlib import Path
from typing import Any

import numpy as np
from dotenv import load_dotenv
from qdrant_client import QdrantClient, models


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SHARED_ENV_FILE = PROJECT_ROOT / ".env"
if not SHARED_ENV_FILE.exists():
    SHARED_ENV_FILE = PROJECT_ROOT / "travel-web" / ".env"
load_dotenv(SHARED_ENV_FILE, override=False)
KNOWLEDGE_BASE_PATH = Path(os.getenv(
    "RAG_KNOWLEDGE_BASE_PATH",
    str(PROJECT_ROOT / "dist" / "data" / "rag-knowledge-base.json"),
))
VECTOR_STORE_PATH = Path(os.getenv(
    "RAG_VECTOR_STORE_PATH",
    str(PROJECT_ROOT / ".private" / "qdrant"),
))
MODEL_NAME = os.getenv("BGE_M3_MODEL", "BAAI/bge-m3")
COLLECTION_NAME = "thai_nguyen_travel_bge_m3"
MAX_CHUNK_CHARS = 1_800
CHUNK_OVERLAP_CHARS = 220
EXCLUDED_TYPES = {
    "tour_demo_departure",
    "tour_booking_options",
    "booking_global_rules",
    "tour_full_record",
}


def _sentence_chunks(text: str, max_chars: int = MAX_CHUNK_CHARS, overlap_chars: int = CHUNK_OVERLAP_CHARS) -> list[str]:
    content = str(text or "").strip()
    if len(content) <= max_chars:
        return [content]

    sentences = re.findall(r"[^.!?\n]+[.!?\n]*", content)
    chunks: list[str] = []
    current = ""
    for raw in sentences or [content]:
        sentence = raw.strip()
        if not sentence:
            continue
        if current and len(current) + len(sentence) + 1 > max_chars:
            chunks.append(current.strip())
            tail = current[-overlap_chars:]
            boundary = re.search(r"[.!?]\s", tail)
            current = f"{tail[boundary.start() + 1:] if boundary else tail} {sentence}".strip()
            if len(current) > max_chars:
                chunks.append(current[:max_chars])
                current = current[max_chars - overlap_chars:]
        else:
            current = f"{current} {sentence}" if current else sentence
    if current.strip():
        chunks.append(current.strip())

    bounded: list[str] = []
    for chunk in chunks:
        while len(chunk) > max_chars:
            cut = chunk.rfind(" ", 0, max_chars + 1)
            if cut < max_chars * 0.75:
                cut = max_chars
            bounded.append(chunk[:cut].strip())
            chunk = chunk[max(1, cut - overlap_chars):].strip()
        if chunk:
            bounded.append(chunk)
    return bounded


def _build_chunks(knowledge_base: dict[str, Any]) -> list[dict[str, Any]]:
    documents = knowledge_base.get("documents")
    if not isinstance(documents, list):
        raise ValueError("Knowledge base must contain a documents array.")

    chunks: list[dict[str, Any]] = []
    for doc in documents:
        metadata = doc.get("metadata") or {}
        if metadata.get("document_type") in EXCLUDED_TYPES:
            continue
        content = str(doc.get("page_content") or "")
        parts = _sentence_chunks(content)
        for index, page_content in enumerate(parts):
            chunk_id = str(doc.get("id") or f"doc-{len(chunks)}")
            if len(parts) > 1:
                chunk_id = f"{chunk_id}#{index + 1}"
            chunks.append({"id": chunk_id, "page_content": page_content, "metadata": metadata})
    return chunks


def _embedding_text(chunk: dict[str, Any]) -> str:
    metadata = chunk["metadata"]
    labels = [
        f"Tiêu đề: {metadata.get('title', '')}",
        f"Mã: {metadata.get('code', '')}",
        f"Địa điểm: {'; '.join(metadata.get('destinations') or [])}",
    ]
    return "\n".join([*labels, chunk["page_content"]])


class BgeM3VectorIndex:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._client: QdrantClient | None = None
        self._model: Any = None
        self._ready = False
        self._chunk_count = 0
        self._source_fingerprint = ""

    def _load_model(self) -> Any:
        if self._model is not None:
            return self._model

        import torch
        from FlagEmbedding import BGEM3FlagModel

        use_fp16 = torch.cuda.is_available()
        print(f"Loading BGE-M3 model {MODEL_NAME} ({'CUDA' if use_fp16 else 'CPU'}). First start may download model weights.")
        self._model = BGEM3FlagModel(
            MODEL_NAME,
            use_fp16=use_fp16,
            devices=["cuda:0"] if use_fp16 else ["cpu"],
        )
        return self._model

    def _encode(self, texts: list[str]) -> np.ndarray:
        output = self._load_model().encode(
            texts,
            batch_size=8,
            max_length=1024,
            return_dense=True,
            return_sparse=False,
            return_colbert_vecs=False,
        )
        vectors = np.asarray(output["dense_vecs"], dtype=np.float32)
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        return vectors / np.maximum(norms, 1e-12)

    def _fingerprint(self, source_bytes: bytes) -> str:
        digest = hashlib.sha256()
        digest.update(source_bytes)
        digest.update(f"\n{MODEL_NAME}\n{MAX_CHUNK_CHARS}\n{CHUNK_OVERLAP_CHARS}".encode())
        return digest.hexdigest()

    def ensure_ready(self) -> None:
        with self._lock:
            if self._ready:
                return
            if not KNOWLEDGE_BASE_PATH.is_file():
                raise FileNotFoundError(f"RAG knowledge base not found: {KNOWLEDGE_BASE_PATH}")

            source_bytes = KNOWLEDGE_BASE_PATH.read_bytes()
            fingerprint = self._fingerprint(source_bytes)
            knowledge_base = json.loads(source_bytes)
            chunks = _build_chunks(knowledge_base)
            if not chunks:
                raise ValueError("RAG knowledge base contains no searchable chunks.")

            self._load_model()
            VECTOR_STORE_PATH.mkdir(parents=True, exist_ok=True)
            self._client = QdrantClient(path=str(VECTOR_STORE_PATH))
            must_rebuild = not self._collection_matches(fingerprint, len(chunks))
            if must_rebuild:
                print(f"Building BGE-M3 vectors for {len(chunks)} RAG chunks.")
                self._rebuild_collection(chunks, fingerprint)
                print("BGE-M3 Qdrant index build complete.")
            else:
                print(f"Reused persistent BGE-M3 Qdrant index with {len(chunks)} chunks.")

            self._source_fingerprint = fingerprint
            self._chunk_count = len(chunks)
            self._ready = True

    def _collection_matches(self, fingerprint: str, expected_count: int) -> bool:
        assert self._client is not None
        if not self._client.collection_exists(COLLECTION_NAME):
            return False
        info = self._client.get_collection(COLLECTION_NAME)
        if info.points_count != expected_count:
            return False
        points, _ = self._client.scroll(
            COLLECTION_NAME,
            limit=1,
            with_payload=True,
            with_vectors=False,
        )
        return bool(points and points[0].payload and points[0].payload.get("source_fingerprint") == fingerprint)

    def _rebuild_collection(self, chunks: list[dict[str, Any]], fingerprint: str) -> None:
        assert self._client is not None
        vectors = self._encode([_embedding_text(chunk) for chunk in chunks])
        if self._client.collection_exists(COLLECTION_NAME):
            self._client.delete_collection(COLLECTION_NAME)

        vector_size = int(vectors.shape[1])
        self._client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
        )
        batch_size = 32
        for start in range(0, len(chunks), batch_size):
            points = []
            for index in range(start, min(start + batch_size, len(chunks))):
                chunk = chunks[index]
                points.append(models.PointStruct(
                    id=str(uuid.uuid5(uuid.NAMESPACE_URL, chunk["id"])),
                    vector=vectors[index].tolist(),
                    payload={
                        "chunk_id": chunk["id"],
                        "page_content": chunk["page_content"],
                        "metadata": chunk["metadata"],
                        "source_fingerprint": fingerprint,
                    },
                ))
            self._client.upsert(collection_name=COLLECTION_NAME, points=points, wait=True)

    def search(self, query: str, limit: int = 12) -> dict[str, Any]:
        self.ensure_ready()
        assert self._client is not None
        query_vector = self._encode([query])[0].tolist()
        result = self._client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            limit=max(1, min(int(limit), 30)),
            with_payload=True,
            with_vectors=False,
        )
        matches = []
        for point in result.points:
            payload = point.payload or {}
            matches.append({
                "id": payload.get("chunk_id", ""),
                "page_content": payload.get("page_content", ""),
                "metadata": payload.get("metadata", {}),
                "score": float(point.score or 0.0),
            })
        return {"matches": matches, "model": MODEL_NAME, "chunk_count": self._chunk_count}

    def health(self) -> dict[str, Any]:
        return {
            "ready": self._ready,
            "model": MODEL_NAME,
            "vector_store": "qdrant-local",
            "index_path": str(VECTOR_STORE_PATH),
            "chunk_count": self._chunk_count,
        }


_vector_index = BgeM3VectorIndex()


def initialize_rag_index() -> dict[str, Any]:
    _vector_index.ensure_ready()
    return _vector_index.health()


def retrieve_rag_chunks(query: str, limit: int = 12) -> dict[str, Any]:
    return _vector_index.search(query, limit)


def rag_index_health() -> dict[str, Any]:
    return _vector_index.health()
