"""
Configuration settings and dual LLM initialization (Ollama + Groq Cloud).
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Prefer the monorepo root .env; support the planner's previous sibling layout too.
PLANNER_ROOT = Path(__file__).resolve().parents[1]
SHARED_ENV_FILE = PLANNER_ROOT.parent / ".env"
if not SHARED_ENV_FILE.exists():
    SHARED_ENV_FILE = PLANNER_ROOT.parent / "travel-web" / ".env"
load_dotenv(SHARED_ENV_FILE, override=False)

# Ollama settings
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:4b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Groq Cloud settings (for free cloud deployment)
GROQ_API_KEYS = tuple(dict.fromkeys(
    value.strip()
    for name in ("GROQ_API_KEY", *(f"GROQ_API_KEY_{index}" for index in range(1, 7)))
    if (value := os.getenv(name, "").strip())
))
GROQ_MODEL = os.getenv("PLANNER_GROQ_MODEL", os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"))
_groq_key_cursor = 0

# Public catalog retrieval bounds; the final recommendation limit is independent.
MYTHAINGUYEN_MAX_PAGES = max(1, min(int(os.getenv("MYTHAINGUYEN_MAX_PAGES", "5")), 20))
MYTHAINGUYEN_MAX_DETAILS = max(1, min(int(os.getenv("MYTHAINGUYEN_MAX_DETAILS", "18")), 30))
PLACE_SOURCE_TIMEOUT_SECONDS = max(2, min(int(os.getenv("PLACE_SOURCE_TIMEOUT_SECONDS", "8")), 30))
THAI_NGUYEN_SOURCE_BUDGET_SECONDS = max(10, min(int(os.getenv("THAI_NGUYEN_SOURCE_BUDGET_SECONDS", "35")), 60))
NOMINATIM_BASE_URL = os.getenv("NOMINATIM_BASE_URL", "https://nominatim.openstreetmap.org").rstrip("/")
NOMINATIM_USER_AGENT = os.getenv(
    "NOMINATIM_USER_AGENT", "Multi-Agent-AI-Travel-Planner/1.0"
).strip()


def get_llm(json_mode: bool = False, num_predict: int = 1200, temperature: float = 0.3, num_ctx: int = 4096):
    """
    Returns Groq if one or more GROQ_API_KEY values are configured (Cloud hosting),
    otherwise falls back to local Ollama.
    """
    if GROQ_API_KEYS:
        from langchain_groq import ChatGroq
        model_kwargs = {"response_format": {"type": "json_object"}} if json_mode else {}

        class RotatingGroqChat:
            def invoke(self, messages, *args, **kwargs):
                global _groq_key_cursor
                start = _groq_key_cursor % len(GROQ_API_KEYS)
                last_error = None
                for offset in range(len(GROQ_API_KEYS)):
                    key_index = (start + offset) % len(GROQ_API_KEYS)
                    llm = ChatGroq(
                        model=GROQ_MODEL,
                        groq_api_key=GROQ_API_KEYS[key_index],
                        temperature=temperature,
                        max_tokens=num_predict,
                        model_kwargs=model_kwargs,
                        timeout=30,
                        max_retries=0,
                    )
                    try:
                        response = llm.invoke(messages, *args, **kwargs)
                        _groq_key_cursor = key_index + 1
                        return response
                    except Exception as error:
                        last_error = error
                        status = getattr(error, "status_code", None) or getattr(getattr(error, "response", None), "status_code", None)
                        code = str(getattr(error, "code", "")).lower()
                        if status != 429 and "rate_limit" not in code and "insufficient_quota" not in code:
                            raise
                        print(f"Groq planner key {key_index + 1} reached its limit; trying the next configured key.")
                raise last_error

        return RotatingGroqChat()

    # Local Ollama fallback
    from langchain_ollama import ChatOllama
    return ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=temperature,
        reasoning=False,
        format="json" if json_mode else "",
        num_predict=num_predict,
        num_ctx=num_ctx,
        keep_alive="30m",
    )
