"""Multi-source destination discovery shared by the Web API and LangGraph CLI."""
from __future__ import annotations

import json
import hashlib
import logging
import math
import re
import threading
import time
import unicodedata
import urllib.parse
import urllib.request
import urllib.error
from functools import lru_cache
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Optional

from langchain_core.messages import SystemMessage, HumanMessage
from src.config import get_llm, MYTHAINGUYEN_MAX_PAGES, NOMINATIM_BASE_URL, NOMINATIM_USER_AGENT
from src.config import PLACE_SOURCE_TIMEOUT_SECONDS
from src.tools.mythainguyen import fetch_mythainguyen_places, cached_fetch, cached_fetched_at

SOURCE_MAX_PAGES = MYTHAINGUYEN_MAX_PAGES
SOURCE_TIMEOUT = PLACE_SOURCE_TIMEOUT_SECONDS
_nominatim_lock = threading.Lock()
_last_nominatim_request = 0.0
_nominatim_blocked_until = 0.0
_geo_cache: dict[str, tuple[float, dict[str, Any]]] = {}
_GEO_CACHE_TTL = 7 * 24 * 60 * 60
_search_local = threading.local()
_geocode_local = threading.local()
_logger = logging.getLogger(__name__)
_GEO_NO_RESULT_TTL = 15 * 60
_GEO_REJECTED_TTL = 15 * 60
_GEO_SERVICE_ERROR_TTL = 30
_NOMINATIM_MAX_QUERIES = 3
_NOMINATIM_MAX_RETRIES = 1
_NOMINATIM_MIN_INTERVAL = 1.0


def get_places_notice() -> str:
    return getattr(_search_local, "notice", "")


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", (value or "").replace("đ", "d").replace("Đ", "D"))
    return " ".join("".join(c for c in value if not unicodedata.combining(c)).casefold().split())


def _name_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", normalize_text(value)).strip()


def _source_aliases(aliases: list[str] | str | None) -> list[str]:
    if isinstance(aliases, str):
        aliases = [aliases]
    return [value.strip() for value in (aliases or []) if isinstance(value, str) and value.strip()]


def _dedupe_query_parts(*parts: str | None) -> str:
    """Join address components without repeating the same place/admin name."""
    result, seen = [], set()
    for part in parts:
        cleaned = re.sub(r"\s+", " ", (part or "")).strip(" ,;")
        key = normalize_text(cleaned)
        if not key or key in seen:
            continue
        # Avoid appending a component already present as a complete phrase.
        if any(key in previous or previous in key for previous in seen):
            continue
        seen.add(key)
        result.append(cleaned)
    return ", ".join(result)


_DESCRIPTIVE_PREFIXES = (
    r"khu di tích lịch sử", r"khu di tích", r"di tích lịch sử", r"di tích",
    r"danh lam thắng cảnh", r"điểm du lịch",
)


def _name_variants(name: str, namedetails: dict[str, Any] | None = None) -> list[str]:
    without_notes = re.sub(r"\s*\([^)]*\)", " ", name)
    variants = [name, without_notes]
    for base in (without_notes, name):
        for prefix in _DESCRIPTIVE_PREFIXES:
            shortened = re.sub(rf"^\s*{prefix}\s*[:–—-]?\s*", "", base, flags=re.I)
            if normalize_text(shortened) != normalize_text(base):
                variants.append(shortened)
    if namedetails:
        for value in namedetails.values():
            if isinstance(value, str) and value.strip():
                variants.append(value)
            elif isinstance(value, list):
                variants.extend(x for x in value if isinstance(x, str) and x.strip())
    # Bengaluru and Bangalore are current/legacy spellings used across
    # Wikipedia and OpenStreetMap for the same city and its landmarks.
    for variant in list(variants):
        if re.search(r"\bbengaluru\b", variant, re.I):
            variants.append(re.sub(r"\bbengaluru\b", "Bangalore", variant, flags=re.I))
        if re.search(r"\bbangalore\b", variant, re.I):
            variants.append(re.sub(r"\bbangalore\b", "Bengaluru", variant, flags=re.I))
    output, seen = [], set()
    for variant in variants:
        clean = re.sub(r"\s+", " ", variant).strip(" ,.;:()")
        key = _name_key(clean)
        if key and key not in seen:
            seen.add(key)
            output.append(clean)
    return output


def stable_place_id(name: str, address: str | None = None, discriminator: str | None = None) -> str:
    stem = normalize_text(name)
    stem = re.sub(r"[^a-z0-9]+", "-", stem).strip("-") or "place"
    suffix = re.sub(r"[^a-z0-9]+", "-", normalize_text(address or discriminator or ""))[-32:].strip("-")
    return f"{stem}-{suffix}" if suffix else stem


def _wiki_search(destination: str, language: str, limit: int = 30) -> list[dict[str, Any]]:
    query = f"điểm du lịch {destination}" if language == "vi" else f"tourist attractions in {destination}"
    params = urllib.parse.urlencode({"action": "query", "list": "search", "srsearch": query,
                                    "srlimit": limit, "srprop": "", "format": "json"})
    api = f"https://{language}.wikipedia.org/w/api.php?{params}"
    data = json.loads(cached_fetch(api, ttl=1800))
    if data.get("error"):
        raise RuntimeError(f"Wikipedia search error: {data['error'].get('code', 'unknown')}")
    results = data.get("query", {}).get("search", [])
    titles = [x.get("title", "") for x in results if x.get("title") and not any(
        marker in x.get("title", "").casefold() for marker in ("tourism in", "list of", "history of", "transport in", "du lịch tỉnh")
    )]
    if not titles:
        return []
    extract_params = urllib.parse.urlencode({"action": "query", "prop": "extracts|info|coordinates",
                                             "exintro": 1, "explaintext": 1, "inprop": "url",
                                             "titles": "|".join(titles), "format": "json"})
    detail = json.loads(cached_fetch(f"https://{language}.wikipedia.org/w/api.php?{extract_params}", ttl=3600))
    if detail.get("error"):
        raise RuntimeError(f"Wikipedia article error: {detail['error'].get('code', 'unknown')}")
    fetched_at = cached_fetched_at(f"https://{language}.wikipedia.org/w/api.php?{extract_params}") or datetime.now(timezone.utc).isoformat()
    pages = detail.get("query", {}).get("pages", {})
    places = []
    for page in pages.values():
        title, extract = page.get("title", ""), page.get("extract", "").strip()
        if not title or not extract:
            continue
        coords = page.get("coordinates", [{}])[0] if page.get("coordinates") else {}
        places.append({"name": title, "introduction": extract, "latitude": coords.get("lat"),
                       "longitude": coords.get("lon"), "pageid": page.get("pageid"),
                       "url": page.get("fullurl") or f"https://{language}.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}",
                       "language": language, "retrieved_at": fetched_at})
    return places


def fetch_notable_places_wikipedia(destination: str, limit: int = 30) -> list[dict[str, Any]]:
    """Fetch article IDs, canonical URLs, extracts and article coordinates (when present)."""
    results = []
    # Vietnam destinations get Vietnamese articles first; English remains a parallel supplement.
    # Avoid querying the Vietnamese Wikipedia for destinations entered in
    # another language (for example Bengaluru); accented/local Vietnamese
    # names keep the existing Vietnamese-first supplement behavior.
    vietnamese_name = any(char in (destination or "").casefold() for char in "ăâđêôơưáàảãạấầẩẫậắằẳẵặéèẻẽẹếềểễệíìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ")
    languages = ("vi", "en") if vietnamese_name else ("en",)
    failed_languages = []
    for lang in languages:
        try:
            results.extend(_wiki_search(destination, lang, limit))
        except Exception as exc:
            failed_languages.append(lang)
            print(f"[Wikipedia warning] {lang} search unavailable: {exc}")
    if not results and failed_languages:
        _search_local.notice = (
            f"Không tải được dữ liệu Wikipedia cho {destination}. "
            "Đây là lỗi nguồn địa điểm; vui lòng kiểm tra Internet và thử tìm lại."
        )
    return results


def _nominatim_name_labels(hit: dict[str, Any]) -> list[str]:
    values = [hit.get("name")]
    namedetails = hit.get("namedetails")
    if isinstance(namedetails, dict):
        values.extend(namedetails.values())
    labels = []
    for value in values:
        if isinstance(value, str):
            labels.append(_name_key(value))
        elif isinstance(value, list):
            labels.extend(_name_key(item) for item in value if isinstance(item, str))
    return [label for label in labels if label]


def _nominatim_region_context(hit: dict[str, Any]) -> str:
    address = hit.get("address") if isinstance(hit.get("address"), dict) else {}
    values = [str(value) for value in address.values() if isinstance(value, (str, int, float))]
    values.append(str(hit.get("display_name", "")))
    return " " + re.sub(r"[^a-z0-9]+", " ", normalize_text(" ".join(values))) + " "


def _geographic_evidence(hit: dict[str, Any], destination: str, source_address: str | None) -> tuple[bool, str]:
    address = hit.get("address") if isinstance(hit.get("address"), dict) else {}
    context = _nominatim_region_context(hit)
    country_code = normalize_text(str(address.get("country_code", "")))
    if _mytn_requested(destination):
        if country_code != "vn":
            return False, "country_not_confirmed"
        if " thai nguyen " not in context and " thainguyen " not in context:
            return False, "destination_not_confirmed"
        expected = normalize_text(source_address or "")
        localities = ("dinh hoa", "phu luong", "pho yen", "song cong", "dai tu", "dong hy", "vo nhai", "phu binh")
        expected_locality = next((name for name in localities if name in expected), None)
        if expected_locality and expected_locality not in context:
            return False, "source_locality_not_confirmed"
        return True, "country_destination_and_source_locality_match"
    meaningful = [token for token in normalize_text(destination).split()
                  if token not in {"city", "district", "province", "vietnam", "tp", "thanh", "pho"}]
    if meaningful and all(token in context for token in meaningful):
        return True, "destination_name_match"
    if not meaningful:
        return True, "destination_not_constrained"
    return False, "destination_not_confirmed"


_ADMIN_RESULT_TYPES = {"country", "state", "city", "district", "county", "locality", "suburb", "postcode", "street", "quarter", "house", "residential", "address"}
_ALLOWED_NOMINATIM_CATEGORIES = {"tourism", "historic", "leisure", "natural", "man_made", "amenity", "building"}


def _nominatim_result_type(hit: dict[str, Any]) -> str:
    category = normalize_text(str(hit.get("category", "")))
    object_type = normalize_text(str(hit.get("type", "")))
    address_type = normalize_text(str(hit.get("addresstype", "")))
    if address_type in _ADMIN_RESULT_TYPES and category not in _ALLOWED_NOMINATIM_CATEGORIES:
        return address_type
    if category not in _ALLOWED_NOMINATIM_CATEGORIES:
        return category or address_type or object_type
    return category


def _name_matches(hit: dict[str, Any], place_name: str, aliases: list[str] | None = None) -> tuple[bool, bool]:
    expected = [_name_key(x) for x in [place_name, *_name_variants(place_name), *_source_aliases(aliases)] if x]
    labels = _nominatim_name_labels(hit)
    exact = any(label == wanted for label in labels for wanted in expected if wanted)
    matched = exact or any(wanted and (f" {wanted} " in f" {label} ") for label in labels for wanted in expected)
    return matched, exact


def _valid_geocode_hit(hit: dict[str, Any], place_name: str, destination: str,
                       source_address: str | None = None, aliases: list[str] | None = None) -> tuple[float, float] | None:
    if not isinstance(hit, dict):
        return None
    point = _coordinate_pair(hit.get("lat"), hit.get("lon"))
    if point is None or not _name_matches(hit, place_name, aliases)[0]:
        return None
    category = normalize_text(str(hit.get("category", "")))
    object_type = normalize_text(str(hit.get("type", "")))
    address_type = normalize_text(str(hit.get("addresstype", "")))
    result_type = _nominatim_result_type(hit)
    if result_type not in _ALLOWED_NOMINATIM_CATEGORIES or address_type in _ADMIN_RESULT_TYPES or object_type in _ADMIN_RESULT_TYPES:
        return None
    if category == "building" and object_type in {"yes", "house", "apartments", "residential"} and not _name_matches(hit, place_name, aliases)[1]:
        return None
    in_scope, _ = _geographic_evidence(hit, destination, source_address)
    return point if in_scope else None


def _geocode_hit_rejection_reason(hit: dict[str, Any], place_name: str, destination: str,
                                  source_address: str | None, aliases: list[str] | None = None) -> str:
    if not isinstance(hit, dict) or _coordinate_pair(hit.get("lat"), hit.get("lon")) is None:
        return "invalid_coordinates"
    if not _name_matches(hit, place_name, aliases)[0]:
        return "name_mismatch"
    category = normalize_text(str(hit.get("category", "")))
    object_type = normalize_text(str(hit.get("type", "")))
    address_type = normalize_text(str(hit.get("addresstype", "")))
    result_type = _nominatim_result_type(hit)
    if result_type not in _ALLOWED_NOMINATIM_CATEGORIES or address_type in _ADMIN_RESULT_TYPES or object_type in _ADMIN_RESULT_TYPES:
        return "inappropriate_object_type"
    in_scope, reason = _geographic_evidence(hit, destination, source_address)
    return reason if not in_scope else "unverified_result"


def _geocode_queries(place_name: str, destination: str, address: str | None,
                     aliases: list[str] | None = None) -> list[str]:
    locality = "Thái Nguyên" if _mytn_requested(destination) else destination
    country = "Vietnam" if _mytn_requested(destination) else None
    queries = [_dedupe_query_parts(place_name, address, locality, country),
               _dedupe_query_parts(place_name, locality, country)]
    queries.extend(_dedupe_query_parts(alias, address, locality, country) for alias in _source_aliases(aliases))
    variants = _name_variants(place_name)
    queries.extend(_dedupe_query_parts(variant, address, locality, country) for variant in variants[1:])
    return list(dict.fromkeys(q for q in queries if q))[:_NOMINATIM_MAX_QUERIES]


def _parse_retry_after(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        try:
            from email.utils import parsedate_to_datetime
            return max(0.0, (parsedate_to_datetime(value) - datetime.now(timezone.utc)).total_seconds())
        except (TypeError, ValueError, OverflowError):
            return None


def _nominatim_request(query: str, destination: str) -> list[dict[str, Any]]:
    """Request one bounded Nominatim search, respecting process-local pacing."""
    global _last_nominatim_request, _nominatim_blocked_until
    params = {"q": query, "format": "jsonv2", "addressdetails": 1, "namedetails": 1,
              "limit": 5, "accept-language": "vi,en"}
    if _mytn_requested(destination):
        params["countrycodes"] = "vn"
    endpoint = f"{NOMINATIM_BASE_URL}/search?{urllib.parse.urlencode(params)}"
    for attempt in range(_NOMINATIM_MAX_RETRIES + 1):
        with _nominatim_lock:
            now = time.monotonic()
            if now < _nominatim_blocked_until:
                raise RuntimeError("rate_limited")
            delay = _NOMINATIM_MIN_INTERVAL - (now - _last_nominatim_request)
            if delay > 0:
                time.sleep(delay)
            request = urllib.request.Request(endpoint, headers={"Accept": "application/json", "User-Agent": NOMINATIM_USER_AGENT})
            _last_nominatim_request = time.monotonic()
            try:
                with urllib.request.urlopen(request, timeout=SOURCE_TIMEOUT) as response:
                    payload = json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                if exc.code == 429:
                    wait = _parse_retry_after(exc.headers.get("Retry-After") if exc.headers else None)
                    if wait is None:
                        wait = 2 ** (attempt + 1)
                    _nominatim_blocked_until = max(_nominatim_blocked_until, time.monotonic() + wait)
                    raise RuntimeError("rate_limited") from None
                if exc.code == 403:
                    raise RuntimeError("access_forbidden") from None
                if 500 <= exc.code < 600 and attempt < _NOMINATIM_MAX_RETRIES:
                    time.sleep(2 ** attempt)
                    continue
                if 500 <= exc.code < 600:
                    raise RuntimeError("service_unavailable") from None
                raise RuntimeError(f"http_{exc.code}") from None
            except (TimeoutError, urllib.error.URLError):
                if attempt < _NOMINATIM_MAX_RETRIES:
                    time.sleep(2 ** attempt)
                    continue
                raise RuntimeError("network_or_timeout") from None
            except (json.JSONDecodeError, UnicodeDecodeError):
                raise RuntimeError("invalid_json") from None
        if not isinstance(payload, list) or any(not isinstance(item, dict) for item in payload):
            raise RuntimeError("invalid_response_schema")
        return payload
    raise RuntimeError("network_or_timeout")


def _nominatim_duplicate_key(hit: dict[str, Any]) -> tuple[Any, ...]:
    if hit.get("osm_type") is not None and hit.get("osm_id") is not None:
        return "osm", str(hit["osm_type"]), str(hit["osm_id"])
    point = _coordinate_pair(hit.get("lat"), hit.get("lon"))
    return "fallback", point, normalize_text(str(hit.get("name", ""))), normalize_text(str(hit.get("category", ""))), normalize_text(str(hit.get("type", "")))


def _geocode_nominatim_place(place_name: str, destination: str, address: str | None = None,
                             retry: bool = False, aliases: list[str] | None = None,
                             place_id: str | None = None) -> dict[str, Any]:
    aliases = _source_aliases(aliases)
    queries = _geocode_queries(place_name, destination, address, aliases)
    country_filter = "vn" if _mytn_requested(destination) else ""
    cache_key = "nominatim:" + normalize_text(" | ".join((NOMINATIM_BASE_URL, " ".join(queries), "vi,en", country_filter)))
    cached = _geo_cache.get(cache_key)
    if cached and cached[0] > time.monotonic() and not (retry and cached[1].get("status") != "nominatim_verified"):
        state = {**cached[1], "cache_hit": True}
        _geocode_local.state = state
        return state
    rejected: list[dict[str, str]] = []
    service_error = None
    for query in queries:
        try:
            hits = _nominatim_request(query, destination)
        except Exception as exc:
            message = str(exc)
            known = {"rate_limited", "access_forbidden", "service_unavailable", "network_or_timeout", "invalid_json", "invalid_response_schema"}
            service_error = message if message in known or message.startswith("http_") else "service_error"
            _logger.warning("nominatim_request_failed", extra={"place_id": place_id, "place_name": place_name, "query": query, "error_type": service_error})
            break
        acceptable, seen = [], set()
        for hit in hits:
            key = _nominatim_duplicate_key(hit)
            if key in seen:
                continue
            seen.add(key)
            point = _valid_geocode_hit(hit, place_name, destination, address, aliases)
            if point is None:
                rejected.append({"name": str(hit.get("name", ""))[:120], "reason": _geocode_hit_rejection_reason(hit, place_name, destination, address, aliases)})
                continue
            exact = _name_matches(hit, place_name, aliases)[1]
            _, geography_reason = _geographic_evidence(hit, destination, address)
            try:
                importance = float(hit.get("importance", 0) or 0)
                if not math.isfinite(importance): importance = 0.0
            except (TypeError, ValueError):
                importance = 0.0
            acceptable.append(((int(exact), importance), point, hit, geography_reason))
        if acceptable:
            acceptable.sort(key=lambda row: row[0], reverse=True)
            if len(acceptable) > 1 and acceptable[0][0] == acceptable[1][0] and acceptable[0][1] != acceptable[1][1]:
                state = {"latitude": None, "longitude": None, "status": "ambiguous", "reason": "multiple_equally_supported_results", "coordinate_source": None}
                _geo_cache[cache_key] = (time.monotonic() + _GEO_REJECTED_TTL, state)
                _geocode_local.state = {**state, "cache_hit": False}
                return state
            _, point, chosen, geography_reason = acceptable[0]
            state = {"latitude": point[0], "longitude": point[1], "status": "nominatim_verified",
                     "reason": "name_type_and_geography_match", "coordinate_source": "Nominatim",
                     "chosen_name": str(chosen.get("name", "")),
                     "match_basis": {"category": chosen.get("category"), "type": chosen.get("type"), "geography": geography_reason},
                     "attribution": chosen.get("licence") or "© OpenStreetMap contributors — https://www.openstreetmap.org/copyright"}
            _geo_cache[cache_key] = (time.monotonic() + _GEO_CACHE_TTL, state)
            _geocode_local.state = {**state, "cache_hit": False}
            return state
    if service_error:
        status, reason = "service_error", service_error
        if service_error != "rate_limited":
            _geo_cache[cache_key] = (time.monotonic() + _GEO_SERVICE_ERROR_TTL, {"latitude": None, "longitude": None, "status": status, "reason": reason, "coordinate_source": None})
    elif rejected:
        status, reason = "rejected", "results_failed_name_type_or_geography_checks"
        _geo_cache[cache_key] = (time.monotonic() + _GEO_REJECTED_TTL, {"latitude": None, "longitude": None, "status": status, "reason": reason, "coordinate_source": None})
    else:
        status, reason = "not_found", "no_results"
        _geo_cache[cache_key] = (time.monotonic() + _GEO_NO_RESULT_TTL, {"latitude": None, "longitude": None, "status": status, "reason": reason, "coordinate_source": None})
    state = {"latitude": None, "longitude": None, "status": status, "reason": reason, "coordinate_source": None, "rejected_candidates": rejected[:5]}
    _geocode_local.state = {**state, "cache_hit": False}
    _logger.info("nominatim_unresolved", extra={"place_id": place_id, "place_name": place_name, "query_count": len(queries), "status": status, "reason": reason, "rejected_candidates": rejected[:5]})
    return state


def geocode_osm_place(place_name: str, destination: str, address: str | None = None, retry: bool = False,
                      aliases: list[str] | None = None, place_id: str | None = None) -> tuple[float | None, float | None, bool]:
    result = _geocode_nominatim_place(place_name, destination, address, retry=retry, aliases=aliases, place_id=place_id)
    return result["latitude"], result["longitude"], result["status"] == "nominatim_verified"


def _mytn_requested(destination: str) -> bool:
    normalized = normalize_text(destination)
    return "thai nguyen" in normalized or "thainguyen" in normalized


def _coordinate_pair(latitude: Any, longitude: Any) -> tuple[float, float] | None:
    try:
        lat, lon = float(latitude), float(longitude)
    except (TypeError, ValueError):
        return None
    if math.isfinite(lat) and math.isfinite(lon) and -90 <= lat <= 90 and -180 <= lon <= 180:
        return lat, lon
    return None


def _coordinate_reference_url(url: str | None) -> str | None:
    try:
        parsed = urllib.parse.urlsplit(url or "")
    except ValueError:
        return None
    if parsed.scheme != "https" or parsed.hostname != "mythainguyen.vn":
        return None
    return urllib.parse.urlunsplit(("https", parsed.netloc.lower(), parsed.path.rstrip("/"), "", ""))


def _coordinate_name_keys(name: str | None) -> set[str]:
    value = str(name or "").strip()
    keys = {_name_key(value)} if value else set()
    without_parenthetical = re.sub(r"\s*\([^)]*\)", "", value).strip()
    if without_parenthetical:
        keys.add(_name_key(without_parenthetical))
    return {key for key in keys if key}


@lru_cache(maxsize=1)
def _mytn_coordinate_reference_index() -> tuple[dict[str, dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    """Load the local MyThaiNguyen coordinate reference file once per process."""
    path = Path(__file__).resolve().parents[2] / "mythainguyen_places.json"
    try:
        with path.open(encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        _logger.warning("mythainguyen_coordinate_reference_unavailable", extra={"error_type": type(exc).__name__})
        return {}, {}
    if not isinstance(payload, dict) or not isinstance(payload.get("places"), list):
        return {}, {}

    by_url: dict[str, dict[str, Any]] = {}
    by_name: dict[str, list[dict[str, Any]]] = {}
    for item in payload["places"]:
        if not isinstance(item, dict) or _coordinate_pair(item.get("latitude"), item.get("longitude")) is None:
            continue
        reference = dict(item)
        source_url = _coordinate_reference_url(item.get("source_url"))
        if source_url:
            by_url[source_url] = reference
        for key in _coordinate_name_keys(item.get("name")):
            by_name.setdefault(key, []).append(reference)
    return by_url, by_name


def _mytn_coordinate_reference(place: dict[str, Any]) -> dict[str, Any] | None:
    """Find a coordinate reference by canonical MyThaiNguyen URL, then exact name."""
    urls = [place.get("url"), *(s.get("url") for s in (place.get("sources") or []) if isinstance(s, dict))]
    by_url, by_name = _mytn_coordinate_reference_index()
    for url in urls:
        key = _coordinate_reference_url(url)
        if key and key in by_url:
            return by_url[key]

    candidates: list[dict[str, Any]] = []
    for key in _coordinate_name_keys(place.get("name")):
        candidates.extend(by_name.get(key, []))
    candidates = list({str(item.get("id")): item for item in candidates}.values())
    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) > 1:
        address = normalize_text(place.get("address") or "")
        matches = [item for item in candidates
                   if address and (normalize_text(item.get("address") or "") in address
                                   or address in normalize_text(item.get("address") or ""))]
        if len(matches) == 1:
            return matches[0]
    return None


def _apply_mytn_coordinate_reference(place: dict[str, Any], destination: str) -> bool:
    if not _mytn_requested(destination) or _coordinate_pair(place.get("latitude"), place.get("longitude")) is not None:
        return False
    reference = _mytn_coordinate_reference(place)
    if not reference:
        return False
    point = _coordinate_pair(reference.get("latitude"), reference.get("longitude"))
    if point is None:
        return False
    place["latitude"], place["longitude"] = point
    place["geocoding_status"] = "reference_coordinates"
    place["geocoding_reason"] = str(reference.get("coordinate_status") or "reference_only")
    place["coordinate_source"] = "mythainguyen_places.json"
    reference_url = reference.get("coordinate_source_url") or reference.get("source_url")
    try:
        parsed_reference_url = urllib.parse.urlsplit(reference_url or "")
        place["coordinate_reference_url"] = reference_url if parsed_reference_url.scheme == "https" else None
    except ValueError:
        place["coordinate_reference_url"] = None
    reference_data = place.get("reference_data")
    if not isinstance(reference_data, dict):
        reference_data = {}
        place["reference_data"] = reference_data
    reference_data["coordinate_reference"] = {
        "status": place["geocoding_reason"], "url": place["coordinate_reference_url"]
    }
    return True


CITY_AREAS = ("Phan Đình Phùng", "Linh Sơn", "Tích Lương", "Gia Sàng", "Quyết Thắng", "Quan Triều", "Tân Cương")


def _in_scope(place: dict[str, Any], destination: str) -> bool:
    query = normalize_text(destination)
    address = normalize_text(place.get("address") or "")
    # An explicitly supplied locality/district constrains the catalog result.
    known_localities = ["dinh hoa", "phu luong", "pho yen", "song cong", "dai tu", "dong hy", "vo nhai", "phu binh", "cho moi", "ba be", "cho don", "bac kan", "phan dinh phung", "linh son", "tich luong", "gia sang", "quyet thang", "quan trieu", "tan cuong"]
    locality = next((x for x in known_localities if normalize_text(x) in query and x not in ("thai nguyen",)), None)
    if locality:
        return normalize_text(locality) in address
    if _mytn_requested(destination) and re.search(r"\b(city|thanh pho|thành phố|tp\.?|urban)\b", query):
        return any(normalize_text(area) in address for area in CITY_AREAS)
    if _mytn_requested(destination):
        return True  # “Thái Nguyên” alone means the provincial destination, not just downtown.

    # Wikipedia search can return loosely related biographies, businesses, or
    # nearby cities. Require the destination to be named in the source-backed
    # article context; the destination's own city/province article is not a POI.
    # A model/user may include a country qualifier or an alternate city name.
    # Match the locality, rather than requiring every country/address token
    # to be repeated in an attraction's introductory paragraph.
    locality = re.sub(r"\([^)]*\)", "", destination).split(",", 1)[0]
    query = re.sub(r"\bbangalore\b", "bengaluru", normalize_text(locality))
    if re.sub(r"\bbangalore\b", "bengaluru", normalize_text(place.get("name", ""))) == query:
        return False
    context = normalize_text(" ".join((place.get("name", ""), place.get("introduction", ""), address)))
    context = re.sub(r"\bbangalore\b", "bengaluru", context)
    meaningful = [token for token in query.split() if token not in {"city", "district", "province", "vietnam", "tp", "thanh", "pho"}]
    return bool(meaningful) and all(token in context for token in meaningful)


def _category_from_source(name: str, body: str) -> str | None:
    text = normalize_text(name + " " + body[:1200])
    non_attraction_evidence = (
        "airline", "airlines", "airways", "air transport", "company", "corporation", "business",
        "politician", "rapper", "singer", "actor", "actress", "mayor", "prime minister", "president",
        "political party", "footballer", "cricketer", "basketball player",
        "university", "school", "software", "record label",
    )
    if any(marker in text for marker in non_attraction_evidence):
        return None
    road_like = re.search(r"\b(?:road|street|avenue|highway|thoroughfare)\b", normalize_text(name))
    landmark_context = any(re.search(rf"\b{re.escape(marker)}\b", text) for marker in (
        "historic street", "shopping street", "tourist attraction", "tourist destination",
        "landmark", "heritage site", "promenade", "market",
    ))
    if road_like and not landmark_context:
        return None
    if any(re.search(rf"\b{re.escape(x)}\b", text) for x in ("chua", "den", "di tich", "lich su", "bao tang", "van hoa", "temple", "museum", "heritage", "palace", "fort", "monument", "shrine", "pagoda", "church", "mosque", "memorial", "landmark", "historic site", "archaeological site")):
        return "Heritage & Architecture"
    if any(re.search(rf"\b{re.escape(x)}\b", text) for x in ("hang dong", "trek", "leo nui", "kham pha", "adventure", "cave", "mountain", "hill", "waterfall")):
        return "Trekking & Adventure"
    if any(re.search(rf"\b{re.escape(x)}\b", text) for x in ("cong vien", "ho", "thac", "sinh thai", "vuon", "park", "lake", "garden", "botanical", "sanctuary", "national park", "nature reserve", "forest", "beach", "zoo")):
        return "Parks & Leisure"
    if any(re.search(rf"\b{re.escape(x)}\b", text) for x in ("am thuc", "food", "culinary")):
        return "Food & Culinary"
    return None


def _merge_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    for candidate in candidates:
        title = normalize_text(candidate.get("name", ""))
        address = normalize_text(candidate.get("address") or "")
        match = None
        for existing in merged:
            same_name = title == normalize_text(existing.get("name", "")) or title in existing.get("aliases_norm", [])
            same_address = address and address == normalize_text(existing.get("address") or "")
            close = False
            if all(candidate.get(k) is not None and existing.get(k) is not None for k in ("latitude", "longitude")):
                close = math.hypot(candidate["latitude"] - existing["latitude"], candidate["longitude"] - existing["longitude"]) < 0.002
            old_source_names = {s.get("name", "") for s in existing.get("sources", [])}
            new_source = candidate.get("source_entry", {}).get("name", "")
            verified_cross_source = same_name and (
                (new_source == "My Thái Nguyên" and any(x.startswith("Wikipedia") for x in old_source_names))
                or (new_source.startswith("Wikipedia") and "My Thái Nguyên" in old_source_names)
            )
            addresses_conflict = bool(address and normalize_text(existing.get("address") or "") and not same_address)
            if same_name and (same_address or (close and not addresses_conflict) or (verified_cross_source and not addresses_conflict)):
                match = existing
                break
        if not match:
            candidate["aliases_norm"] = []
            candidate["source_aliases"] = []
            candidate["sources"] = [candidate["source_entry"]]
            merged.append(candidate)
            continue
        match["sources"].append(candidate["source_entry"])
        if title != normalize_text(match["name"]):
            match["aliases_norm"].append(title)
            source_alias = str(candidate.get("name", "")).strip()
            if source_alias and source_alias not in match.setdefault("source_aliases", []):
                match["source_aliases"].append(source_alias)
        for key in ("introduction", "address", "latitude", "longitude", "category_source", "reference_data"):
            if not match.get(key) and candidate.get(key):
                match[key] = candidate[key]
    return merged


def _score(place: dict[str, Any], interests: list[str]) -> int:
    if not interests:
        return 1
    category = place.get("category", "")
    return 1 if category in interests else 0


def _ai_curate(places: list[dict[str, Any]], interests: list[str], destination: str, limit: int) -> list[dict[str, Any]]:
    if not places:
        return []
    selected: dict[str, dict[str, str]] = {}
    if interests and not _mytn_requested(destination):
        try:
            llm = get_llm(json_mode=True, num_predict=1100, temperature=0.1)
            for start in range(0, len(places), 8):
                batch = places[start:start + 8]
                compact = [{"id": p["id"], "name": p["name"], "category_source": p.get("category"),
                            "introduction": (p.get("introduction") or "")[:300]} for p in batch]
                prompt = {"destination": destination, "interests": interests, "candidates": compact,
                          "task": "Select and rank only supplied IDs. Assign one allowed interest category and write a brief Vietnamese description using only the introduction. Do not infer or create facts.",
                          "output": {"places": [{"id": "candidate id", "category": "one allowed interest", "description": "brief Vietnamese summary"}]}}
                response = llm.invoke([SystemMessage(content="Bạn là bộ lọc điểm đến. Chỉ dùng sự kiện trong nguồn và ID được cung cấp. Trả JSON."),
                                       HumanMessage(content=json.dumps(prompt, ensure_ascii=False))])
                raw = re.sub(r"<think>.*?</think>", "", response.content, flags=re.S).strip()
                fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.S)
                if fenced:
                    raw = fenced.group(1)
                data = json.loads(raw[raw.find("{"):raw.rfind("}") + 1])
                batch_ids = {p["id"] for p in batch}
                for item in data.get("places", []):
                    if item.get("id") in batch_ids and item.get("category") in interests:
                        selected[item["id"]] = {"category": item["category"], "description": str(item.get("description", ""))[:240]}
        except Exception as exc:
            print(f"[Places AI warning] Using source-based matching: {exc}")
    # Source-based ranking is the safe fallback; it does not pad results or invent attractions.
    ordered = list(places) if not interests else sorted(places, key=lambda p: (-_score(p, interests), normalize_text(p["name"])))
    output = []
    for p in ordered:
        ai = selected.get(p["id"], {})
        p["category"] = ai.get("category") or p.get("category") or _category_from_source(p["name"], p.get("introduction") or "")
        body = p.get("introduction") or ""
        snippet = re.split(r"(?<=[.!?。])\s+", body)[0].strip()
        p["description"] = ai.get("description") or snippet[:260] or "Chưa có nội dung giới thiệu trong nguồn."
        if not interests or p["category"] in interests or (not _mytn_requested(destination) and not any(_score(x, interests) for x in places)):
            output.append(p)
        if len(output) >= limit:
            break
    # If the model selected some, honor its validated ranking while keeping source-backed fallback matches.
    model_rank = {place_id: index for index, place_id in enumerate(selected)}
    output.sort(key=lambda p: (p["id"] not in model_rank, model_rank.get(p["id"], len(model_rank)), -_score(p, interests), normalize_text(p["name"])))
    return output[:limit]


def search_places_osm(destination: str, limit: int = 10, interests: Optional[list[str]] = None,
                      trip_requirements: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    destination = (destination or "Bengaluru").strip()
    interests = list(interests) if interests is not None else []
    limit = max(0, min(int(limit), 10 if _mytn_requested(destination) else 20))
    if not limit:
        return []
    _search_local.notice = ""
    gathered: list[dict[str, Any]] = []
    if _mytn_requested(destination):
        from src.config import MYTHAINGUYEN_MAX_DETAILS, THAI_NGUYEN_SOURCE_BUDGET_SECONDS
        source_deadline = time.monotonic() + THAI_NGUYEN_SOURCE_BUDGET_SECONDS
        try:
            retrieval_args = {"max_pages": SOURCE_MAX_PAGES, "max_details": MYTHAINGUYEN_MAX_DETAILS, "deadline": source_deadline}
            if trip_requirements and trip_requirements.get("required_places"):
                retrieval_args["requested_names"] = trip_requirements["required_places"]
            for raw in fetch_mythainguyen_places(**retrieval_args):
                if not _in_scope(raw, destination):
                    continue
                source_url = raw.get("url") or ""
                parsed_source_url = urllib.parse.urlparse(source_url)
                if parsed_source_url.scheme != "https" or parsed_source_url.hostname != "mythainguyen.vn":
                    continue
                source_entry = {"name": "My Thái Nguyên", "url": raw["url"],
                                "retrieved_at": raw.get("retrieved_at") or datetime.now(timezone.utc).isoformat()}
                gathered.append({**raw, "source_entry": source_entry,
                                 "reference_data": {k: raw[k] for k in ("admission_fee_source", "contact_source", "category_source", "services_source") if raw.get(k)}})
        except Exception as exc:
            print(f"[My Thái Nguyên warning] {exc}")
            _search_local.notice = "Không truy cập được mythainguyen.vn. Vui lòng thử lại sau."
        if not gathered and not _search_local.notice:
            _search_local.notice = "mythainguyen.vn hiện chưa cung cấp đủ dữ liệu cho khu vực hoặc tiêu chí này."
        # Thái Nguyên profiles and all factual content must be from the provincial portal.
        wikipedia_places = []
    else:
        try:
            wikipedia_places = fetch_notable_places_wikipedia(destination)
        except Exception as exc:
            print(f"[Wikipedia warning] Source unavailable: {exc}")
            wikipedia_places = []
    for raw in wikipedia_places:
        place = dict(raw)
        place["address"] = None
        source_category = _category_from_source(place.get("name", ""), place.get("introduction", ""))
        if source_category is None or not _in_scope(place, destination):
            continue
        place["category"] = source_category
        place["source_entry"] = {"name": f"Wikipedia ({raw['language']})", "url": raw["url"],
                                 "pageid": raw.get("pageid"), "retrieved_at": raw.get("retrieved_at") or datetime.now(timezone.utc).isoformat()}
        gathered.append(place)
    merged = _merge_candidates(gathered)
    for p in merged:
        p.pop("source_entry", None)
        p["_geocode_aliases"] = list(p.pop("source_aliases", [])) + list(p.pop("aliases_norm", []))
        p["id"] = stable_place_id(p["name"], p.get("address"), p.get("url") or str(p.get("pageid") or ""))
        p["sources"] = p.get("sources", [])
        if _mytn_requested(destination) and (not p["sources"] or any(s.get("name") != "My Thái Nguyên" or urllib.parse.urlparse(s.get("url", "")).hostname != "mythainguyen.vn" for s in p["sources"])):
            continue
        if p.get("latitude") is not None or p.get("longitude") is not None:
            point = _coordinate_pair(p.get("latitude"), p.get("longitude"))
            if point is None:
                p["latitude"] = p["longitude"] = None
                p["geocoding_status"] = "rejected"
                p["geocoding_reason"] = "invalid_source_coordinate_pair"
                p["coordinate_source"] = None
                _logger.warning("source_coordinates_rejected", extra={"place_id": p["id"], "place_name": p["name"],
                    "reason": p["geocoding_reason"]})
            else:
                p["latitude"], p["longitude"] = point
                p["geocoding_status"] = "source_coordinates"
                p["geocoding_reason"] = "valid_coordinates_from_place_source"
                p["coordinate_source"] = p.get("coordinate_source") or (p.get("sources") or [{}])[0].get("name", "source")
                _logger.info("source_coordinates_accepted", extra={"place_id": p["id"], "place_name": p["name"],
                    "coordinate_source": p["coordinate_source"]})
        p["category"] = p.get("category") or _category_from_source(p["name"], " ".join((p.get("category_source") or "", p.get("introduction") or "")))
        if p["category"] is None and _mytn_requested(destination):
            # Profiles from the provincial tourist catalog are themselves a
            # source-backed classification when its local taxonomy is unfamiliar.
            p["category"] = "Heritage & Architecture"
    if trip_requirements:
        from src.tools.intent import rank_for_intent
        for p in merged:
            if p.get("latitude") is None or p.get("longitude") is None:
                _apply_mytn_coordinate_reference(p, destination)
        selected = rank_for_intent(merged, trip_requirements, limit)
        # Source text is preserved; the model explains relevance separately.
        for p in selected:
            p["description"] = (p.get("introduction") or "Chưa có nội dung giới thiệu trong nguồn.")[:260]
    else:
        selected = _ai_curate(merged, interests, destination, limit)
    if not selected and not _mytn_requested(destination) and not _search_local.notice:
        _search_local.notice = (
            f"Chưa tìm thấy địa điểm có nguồn phù hợp với {destination}. "
            "Hãy kiểm tra lại tên thành phố hoặc thử tìm lại."
        )
    if _mytn_requested(destination) and trip_requirements and not selected and not _search_local.notice:
        _search_local.notice = "Chưa có ứng viên phù hợp với mô tả từ dữ liệu nguồn đã lấy. Hãy điều chỉnh yêu cầu hoặc tìm lại."
    if _mytn_requested(destination) and not trip_requirements and len(selected) < limit and not _search_local.notice:
        if selected:
            scope = "khu vực" if not interests else "khu vực và sở thích đã chọn"
            _search_local.notice = f"mythainguyen.vn hiện chỉ có {len(selected)} địa điểm phù hợp với {scope}."
        else:
            scope = "khu vực" if not interests else "khu vực và sở thích đã chọn"
            _search_local.notice = f"mythainguyen.vn hiện không có đủ dữ liệu phù hợp với {scope}."
    for place in selected:
        if place.get("latitude") is None or place.get("longitude") is None:
            _apply_mytn_coordinate_reference(place, destination)
        if place.get("latitude") is None or place.get("longitude") is None:
            _geocode_local.state = {}
            lat, lon, found = geocode_osm_place(place["name"], destination, place.get("address"),
                aliases=place.get("alternative_names") or place.get("aliases") or place.get("_geocode_aliases"), place_id=place.get("id"))
            state = getattr(_geocode_local, "state", {})
            if found:
                place["latitude"], place["longitude"] = lat, lon
                place["geocoding_status"] = "nominatim_verified"
                place["geocoding_reason"] = state.get("reason", "name_type_and_geography_match")
                place["coordinate_source"] = "Nominatim"
                place["coordinate_attribution"] = state.get("attribution")
            else:
                place["geocoding_status"] = state.get("status", "not_found")
                place["geocoding_reason"] = state.get("reason", "no_results")
        place.setdefault("geocoding_status", "unavailable")
    # Return JSON-safe floats and public fields; raw fields remain internal only.
    public = []
    for p in selected:
        lat, lon = p.get("latitude"), p.get("longitude")
        if lat is not None and not -90 <= float(lat) <= 90 or lon is not None and not -180 <= float(lon) <= 180:
            lat = lon = None
        public.append({"id": p["id"], "name": p["name"], "category": p["category"], "description": p["description"],
                       "introduction": p.get("introduction") or "", "address": p.get("address"),
                       "images": p.get("images", []),
                       "latitude": lat, "longitude": lon,
                       "sources": p.get("sources", []), "geocoding_status": p.get("geocoding_status", "unavailable"),
                       "geocoding_reason": p.get("geocoding_reason"), "coordinate_source": p.get("coordinate_source"),
                       "coordinate_reference_url": p.get("coordinate_reference_url"),
                       "coordinate_attribution": p.get("coordinate_attribution"),
                       "reference_data": p.get("reference_data", {})})
        public[-1]["required_for"] = p.get("required_for", [])
        public[-1]["recommendation_reason"] = p.get("recommendation_reason", "")
    return public


def retry_missing_coordinates(places: list[dict[str, Any]], destination: str) -> list[dict[str, Any]]:
    """Retry only missing points using each source-backed name/address pair."""
    for place in places:
        point = _coordinate_pair(place.get("latitude"), place.get("longitude"))
        if point is not None:
            place["latitude"], place["longitude"] = point
            continue
        if place.get("latitude") is not None or place.get("longitude") is not None:
            place["latitude"] = place["longitude"] = None
            place["geocoding_status"] = "rejected"
            place["geocoding_reason"] = "invalid_coordinate_pair"
        if _apply_mytn_coordinate_reference(place, destination):
            continue
        _geocode_local.state = {}
        lat, lon, found = geocode_osm_place(place.get("name", ""), destination, place.get("address"), retry=True,
            aliases=place.get("alternative_names") or place.get("aliases") or place.get("_geocode_aliases") or place.get("reference_data", {}).get("aliases"), place_id=place.get("id"))
        state = getattr(_geocode_local, "state", {})
        if found:
            place["latitude"], place["longitude"] = lat, lon
            place["geocoding_status"] = "nominatim_verified"
            place["geocoding_reason"] = state.get("reason", "name_type_and_geography_match")
            place["coordinate_source"] = "Nominatim"
            place["coordinate_attribution"] = state.get("attribution")
        else:
            place["latitude"] = place["longitude"] = None
            place["geocoding_status"] = state.get("status", "not_found")
            place["geocoding_reason"] = state.get("reason", "no_results")
    return places
