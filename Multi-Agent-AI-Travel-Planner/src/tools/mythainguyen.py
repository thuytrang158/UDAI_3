"""Read-only scraper for the My Thái Nguyên tourist-place catalog.

The list endpoint and its pageIndex/page_size contract were verified in the
site's rendered page script (page size 18, POST GetListPlaceNew).
"""
from __future__ import annotations

import html
import json
import math
import re
import threading
import time
import urllib.parse
import urllib.request
from urllib.parse import urlsplit
from html.parser import HTMLParser
from typing import Any
from src.config import MYTHAINGUYEN_MAX_DETAILS, MYTHAINGUYEN_MAX_PAGES, PLACE_SOURCE_TIMEOUT_SECONDS

BASE = "https://mythainguyen.vn"
LIST_URL = BASE + "/vi/places"
PAGINATION_URL = BASE + "/Modules/TravelPlace/GetListPlaceNew"
USER_AGENT = "Multi-Agent-AI-Travel-Planner/1.0 (public travel-place discovery)"


class Node:
    def __init__(self, tag: str = "", attrs: dict[str, str] | None = None):
        self.tag, self.attrs, self.children = tag, attrs or {}, []

    @property
    def text(self) -> str:
        return " ".join(x for x in (c.text if isinstance(c, Node) else c for c in self.children) if x).strip()

    def descendants(self, tag: str | None = None, cls: str | None = None):
        for child in self.children:
            if not isinstance(child, Node):
                continue
            classes = child.attrs.get("class", "").split()
            if (tag is None or child.tag == tag) and (cls is None or cls in classes):
                yield child
            yield from child.descendants(tag, cls)

    def first(self, tag: str | None = None, cls: str | None = None):
        return next(self.descendants(tag, cls), None)


class TreeParser(HTMLParser):
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root, self.stack = Node("document"), []

    def handle_starttag(self, tag, attrs):
        node = Node(tag, dict(attrs))
        (self.stack[-1].children if self.stack else self.root.children).append(node)
        if tag not in self.VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        if data.strip():
            (self.stack[-1].children if self.stack else self.root.children).append(data)


def parse_html(source: str) -> Node:
    parser = TreeParser()
    parser.feed(source)
    return parser.root


def clean_text(value: str) -> str:
    value = html.unescape(value).replace("\xa0", " ")
    return re.sub(r"\s+", " ", value).strip()


def _get(url: str, data: bytes | None = None, timeout: float = PLACE_SOURCE_TIMEOUT_SECONDS) -> str:
    req = urllib.request.Request(url, data=data, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        final = urlsplit(response.geturl())
        if final.scheme != "https" or final.hostname != urlsplit(url).hostname:
            raise ValueError("Source redirected outside its original HTTPS host")
        return response.read().decode(response.headers.get_content_charset() or "utf-8", "replace")


def _detail_links(document: str) -> list[dict[str, str]]:
    root = parse_html(document)
    rows = []
    for item in root.descendants("li", "item-city"):
        heading = item.first("h3", "place-name")
        link = heading.first("a") if heading else None
        href = urllib.parse.urljoin(BASE, link.attrs.get("href", "")) if link else ""
        if not href.startswith(BASE + "/vi/"):
            continue
        name = clean_text(link.text) if link else ""
        if not name:
            continue
        spans = list(item.descendants("span"))
        address = clean_text(spans[0].text) if spans else ""
        intro = item.first("p", "intro")
        rows.append({"name": name, "address": address, "url": href, "snippet": clean_text(intro.text) if intro else ""})
    return rows


def fetch_catalog(max_pages: int = 4, fetcher=_get, deadline: float | None = None) -> list[dict[str, str]]:
    """Fetch initial list, then follow the verified pageIndex POST until empty/repeated."""
    try:
        initial = _detail_links(fetcher(LIST_URL))
    except Exception:
        # An unavailable source must not look like a successful empty search.
        raise
    rows, seen_pages = list(initial), {tuple(x["url"] for x in initial)}
    # The live page initializes with 18 static items and pageIndex=1. Scroll sets
    # it to 2, then POSTs the same filters plus pageIndex to GetListPlaceNew.
    for page_index in range(2, max(2, max_pages) + 1):
        if deadline is not None and time.monotonic() >= deadline:
            break
        body = urllib.parse.urlencode({
            "placename": "", "pageIndex": page_index, "pricefrom": "", "priceto": "",
            "resservice": "", "restype": "", "arrLocation": "", "sortComment": "",
            "sortLike": "", "sortType": "", "sortDistance": "", "sortAB": "", "currLocation": "",
        }).encode()
        try:
            chunk = _detail_links(fetcher(PAGINATION_URL, data=body))
        except Exception:
            break
        signature = tuple(x["url"] for x in chunk)
        if not chunk or signature in seen_pages:
            break
        seen_pages.add(signature)
        rows.extend(chunk)
    unique, seen = [], set()
    for row in rows:
        if row["url"] not in seen:
            seen.add(row["url"])
            unique.append(row)
    return unique


def _metadata(root: Node, labels: tuple[str, ...]) -> str | None:
    text = root.text
    for label in labels:
        match = re.search(rf"{re.escape(label)}\s*:\s*([^:]+?)(?=\s+(?:Số điện thoại|Thời gian tham quan|Mở cửa|Đóng cửa|Email|Địa chỉ)\s*:|$)", text, re.I)
        if match and match.group(1).strip():
            return clean_text(match.group(1))
    return None


def _coordinate_pair(latitude: Any, longitude: Any) -> tuple[float, float] | None:
    try:
        lat, lon = float(latitude), float(longitude)
    except (TypeError, ValueError):
        return None
    if math.isfinite(lat) and math.isfinite(lon) and -90 <= lat <= 90 and -180 <= lon <= 180:
        return lat, lon
    return None


def _nodes_with_context(root: Node, ancestors: tuple[Node, ...] = ()):
    for child in root.children:
        if not isinstance(child, Node):
            continue
        yield child, ancestors
        yield from _nodes_with_context(child, (*ancestors, child))


def _is_related_content(ancestors: tuple[Node, ...]) -> bool:
    markers = ("related", "recommend", "suggest", "tour", "nearby", "similar", "lien-quan", "goi-y", "tour-item")
    return any(any(marker in (node.attrs.get("class", "") + " " + node.attrs.get("id", "")).casefold() for marker in markers)
               for node in ancestors)


def _object_coordinates(root: Node) -> tuple[float, float] | None:
    """Read coordinates attached to a place node or an object-pin map URL.

    Google ``@lat,lon,zoom`` and map ``center`` parameters are viewport centers,
    so they are deliberately ignored.
    """
    lat_keys = ("data-lat", "data-latitude")
    lon_keys = ("data-lng", "data-lon", "data-longitude")
    for node, ancestors in _nodes_with_context(root):
        if _is_related_content((*ancestors, node)):
            continue
        attrs = node.attrs
        lat = next((attrs.get(key) for key in lat_keys if attrs.get(key)), None)
        lon = next((attrs.get(key) for key in lon_keys if attrs.get(key)), None)
        pair = _coordinate_pair(lat, lon) if lat is not None and lon is not None else None
        if pair:
            return pair
    # Only inspect links with an explicit object coordinate marker. Never use
    # the @lat,lon viewport shorthand, map center, bbox, or unrelated text.
    for node, ancestors in _nodes_with_context(root):
        if node.tag != "a" or _is_related_content((*ancestors, node)):
            continue
        href = urllib.parse.unquote(node.attrs.get("href", ""))
        matches = [
            re.search(r"!3d(-?\d+(?:\.\d+)?)!4d(-?\d+(?:\.\d+)?)", href),
            re.search(r"/(?:place/)?(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)(?:[/?#]|$)", href),
        ]
        parsed = urllib.parse.urlsplit(href)
        for key, values in urllib.parse.parse_qs(parsed.query).items():
            if key.casefold() not in {"q", "query", "destination"}:
                continue
            raw = values[0] if values else ""
            matches.append(re.fullmatch(r"\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*", raw))
        for match in matches:
            if match:
                pair = _coordinate_pair(match.group(1), match.group(2))
                if pair:
                    return pair
    return None


def parse_detail(document: str, url: str, list_row: dict[str, str] | None = None) -> dict[str, Any]:
    root = parse_html(document)
    # The live detail page puts its official name in the .example5 hero, while
    # the first h2 is the generic “Giới thiệu” heading.
    hero = next((x for x in root.descendants("div") if "example5" in x.attrs.get("class", "").split()), None)
    title = hero if hero and hero.text else (root.first("h1") or root.first("h2"))
    name = clean_text(title.text) if title else ""
    if not name or name.casefold() in {"giới thiệu", "gioi thieu"} or name.startswith("THAM QUAN"):
        name = (list_row or {}).get("name", "")

    modal = next((x for x in root.descendants("div") if x.attrs.get("id") == "myModal1"), None)
    body = modal.first("div", "cls_modal-body") if modal else None
    paragraphs = [clean_text(p.text) for p in body.descendants("p")] if body else []
    introduction = "\n\n".join(dict.fromkeys(p for p in paragraphs if p and p.lower() != "giới thiệu"))
    if not introduction:
        # Fallback is limited to the content region before the map/reviews.
        text = root.text
        match = re.search(r"Giới thiệu\s+(.*?)\s+(?:Bản đồ|Nhận xét và đánh giá)", text, re.I)
        introduction = clean_text(match.group(1)) if match else (list_row or {}).get("snippet", "")
    # Never treat embedded tour cards, restaurants, or related places as intro.
    introduction = re.sub(r"\s+Xem thêm\s*$", "", introduction)
    address = _metadata(root, ("Địa chỉ",)) or (list_row or {}).get("address") or None
    text = root.text
    type_match = re.search(r"Loại hình du lịch\s*:\s*([^:]+?)(?=\s+(?:Dịch vụ|Giá vé|Địa chỉ|Số điện thoại)\s*:|$)", text, re.I)
    services_match = re.search(r"DỊCH VỤ PHỔ BIẾN\s+(.*?)\s+(?:THÔNG TIN CHUNG|$)", text, re.I)
    services = [clean_text(x) for x in re.split(r"[,;|]", services_match.group(1)) if clean_text(x)] if services_match else []
    fee_match = re.search(r"Giá vé tham quan\s*:\s*([^\n]+?)(?=\s+Số điện thoại|\s+Thời gian tham quan|\s+Mở cửa|$)", text, re.I)
    fee = clean_text(fee_match.group(1)) if fee_match and clean_text(fee_match.group(1)) not in {"phút", ""} else None
    coords = _object_coordinates(root)
    images = []
    for node in root.descendants():
        if node.tag == "img":
            image_ref = (node.attrs.get("src") or node.attrs.get("data-src") or node.attrs.get("data-original") or node.attrs.get("data-lazy-src") or "").split(",")[0].strip()
            image_url = urllib.parse.urljoin(BASE, image_ref)
            if urllib.parse.urlsplit(image_url).scheme == "https" and image_url not in images:
                images.append(image_url)
    result: dict[str, Any] = {"name": name, "address": address,
                              "category_source": clean_text(type_match.group(1)) if type_match else None,
                              "services_source": services,
                              "introduction": introduction or None, "admission_fee_source": fee,
                              "latitude": coords[0] if coords else None, "longitude": coords[1] if coords else None,
                              "coordinate_source": "mythainguyen_detail" if coords else None,
                              "images": images, "url": url}
    phone = _metadata(root, ("Số điện thoại",))
    email = _metadata(root, ("Email",))
    hours = re.search(r"Mở cửa\s*:\s*(.+?)\s*-\s*Đóng cửa\s*:\s*(.+?)(?=\s+Email:|\s+Địa chỉ:|$)", text, re.I)
    result["contact_source"] = {k: v for k, v in {"phone": phone, "email": email, "hours": clean_text(hours.group(0)) if hours else None}.items() if v}
    return result


_cache: dict[str, tuple[float, Any]] = {}
_cache_fetched_at: dict[str, str] = {}
_cache_lock = threading.Lock()
_source_rate_lock = threading.Lock()
_source_last_request: dict[str, float] = {}


def cached_fetch(url: str, data: bytes | None = None, ttl: int = 3600, deadline: float | None = None) -> str:
    key = url + ("?" + data.decode() if data else "")
    now = time.monotonic()
    with _cache_lock:
        entry = _cache.get(key)
        if entry and entry[0] > now:
            return entry[1]
    last_error = None
    for attempt in range(2):
        try:
            host = urlsplit(url).netloc
            with _source_rate_lock:
                delay = 0.25 - (time.monotonic() - _source_last_request.get(host, 0.0))
                if delay > 0:
                    time.sleep(delay)
                _source_last_request[host] = time.monotonic()
            timeout = PLACE_SOURCE_TIMEOUT_SECONDS
            if deadline is not None:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("MyThaiNguyen collection time budget exceeded")
                timeout = min(timeout, remaining)
            text = _get(url, data=data, timeout=timeout)
            with _cache_lock:
                _cache[key] = (time.monotonic() + ttl, text)
                from datetime import datetime, timezone
                _cache_fetched_at[key] = datetime.now(timezone.utc).isoformat()
            return text
        except Exception as exc:
            last_error = exc
            if attempt == 0:
                time.sleep(.25)
    raise last_error  # type: ignore[misc]


def cached_fetched_at(url: str, data: bytes | None = None) -> str | None:
    key = url + ("?" + data.decode() if data else "")
    with _cache_lock:
        return _cache_fetched_at.get(key)


def fetch_mythainguyen_places(max_pages: int = MYTHAINGUYEN_MAX_PAGES, max_details: int = MYTHAINGUYEN_MAX_DETAILS,
                              deadline: float | None = None, requested_names: list[str] | None = None) -> list[dict[str, Any]]:
    # Every source request uses the shared fetch/cache; concurrency is serialized.
    fetcher = (lambda url, data=None: cached_fetch(url, data=data, deadline=deadline)) if deadline is not None else cached_fetch
    rows = fetch_catalog(max_pages=max_pages, fetcher=fetcher, deadline=deadline)
    if requested_names:
        from src.tools.intent import matches_place
        for name in requested_names:
            if any(matches_place(name, row) for row in rows):
                continue
            if deadline is not None and time.monotonic() >= deadline:
                break
            try:
                query = urllib.parse.urlencode({"placename": name, "pageIndex": 1}).encode()
                targeted = _detail_links(fetcher(PAGINATION_URL, data=query))
                urls = {row["url"] for row in rows}
                rows.extend(row for row in targeted if row["url"] not in urls)
            except Exception:
                pass  # The caller reports any required place still missing; never fabricate it.
        rows.sort(key=lambda row: not any(matches_place(name, row) for name in requested_names))
    places = []
    for index, row in enumerate(rows):
        try:
            if index >= max_details or (deadline is not None and time.monotonic() >= deadline):
                raise TimeoutError("Keep catalog evidence when the detail budget is exhausted")
            detail_html = cached_fetch(row["url"], deadline=deadline)
            detail = parse_detail(detail_html, row["url"], row)
            detail["retrieved_at"] = cached_fetched_at(row["url"])
            places.append(detail)
        except Exception:
            # Keep valid list entries and their truthful snippet when detail fetch fails.
            places.append({"name": row["name"], "address": row["address"] or None,
                           "introduction": row["snippet"] or None, "url": row["url"],
                           "retrieved_at": cached_fetched_at(row["url"]),
                           "category_source": None, "latitude": None, "longitude": None, "coordinate_source": None,
                           "admission_fee_source": None, "contact_source": {}})
    return places
