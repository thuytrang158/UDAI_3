"""Source-grounded AI recommendations and constraints shared by every planning step."""
import json
import math
import re
import unicodedata

from langchain_core.messages import HumanMessage, SystemMessage

from src.config import get_llm
from src.tools.accommodation import extract_json_object


def normalized_name(value):
    value = unicodedata.normalize("NFKD", str(value).replace("đ", "d").replace("Đ", "D"))
    value = " ".join(re.sub(r"[^a-z0-9]+", " ", "".join(c for c in value if not unicodedata.combining(c)).lower()).split())
    return re.sub(r"\batk\b", "an toan khu", value)


def matches_place(requested, place):
    """Match a specific named place, without matching its district/address alone."""
    tokens = set(normalized_name(requested).split())
    labels = [place.get("name", ""), *(place.get("alternative_names") or [])]
    return bool(tokens) and any(tokens <= set(normalized_name(label).split()) for label in labels)


def required_for(place, intent):
    return [name for name in intent.get("required_places", []) if matches_place(name, place)]


def requirement_report(places, intent):
    return [{"requested": name,
             "status": "matched" if any(name in required_for(p, intent) for p in places) else "missing",
             "place_ids": [p["id"] for p in places if name in required_for(p, intent) and p.get("id")]}
            for name in intent.get("required_places", [])]


def validate_selection(places, intent):
    missing = [row["requested"] for row in requirement_report(places, intent) if row["status"] == "missing"]
    excluded = [name for name in intent.get("excluded_places", []) if any(matches_place(name, p) for p in places)]
    if missing:
        raise ValueError("Lịch trình chưa có điểm bạn yêu cầu: " + ", ".join(missing) + ". Hãy chọn điểm này hoặc sửa yêu cầu ở bước 1.")
    if excluded:
        raise ValueError("Lịch trình đang chứa điểm bạn muốn tránh: " + ", ".join(excluded))


def rank_for_intent(places, intent, limit):
    """Have the model score sourced candidates; enforce named constraints before truncation."""
    candidates = [p for p in places if not any(matches_place(name, p) for name in intent.get("excluded_places", []))]
    if not candidates:
        return []
    llm = get_llm(json_mode=True, num_predict=1600, temperature=0.1, num_ctx=8192)
    judgments = {}
    anchors = [p for p in candidates if required_for(p, intent)]

    def anchor_distances(place):
        if any(place.get(key) is None for key in ("latitude", "longitude")):
            return []
        distances = []
        lat, lon = map(math.radians, (place["latitude"], place["longitude"]))
        for anchor in anchors:
            if any(anchor.get(key) is None for key in ("latitude", "longitude")):
                continue
            a_lat, a_lon = map(math.radians, (anchor["latitude"], anchor["longitude"]))
            hav = math.sin((lat-a_lat)/2)**2 + math.cos(lat)*math.cos(a_lat)*math.sin((lon-a_lon)/2)**2
            distances.append({"place": anchor["name"], "straight_line_km": round(6371 * 2 * math.asin(min(1, math.sqrt(hav))), 1)})
        return distances

    for start in range(0, len(candidates), 12):
        batch = candidates[start:start + 12]
        payload = {
            "requirements": intent,
            "required_venues": [{"name": p["name"], "address": p.get("address")} for p in anchors],
            "candidates": [{"id": p["id"], "name": p["name"], "address": p.get("address"),
                            "identity_matches": required_for(p, intent),
                            "distances_to_required": anchor_distances(p),
                            "category": p.get("category"), "introduction": (p.get("introduction") or "")[:350]} for p in batch],
        }
        response = llm.invoke([
            SystemMessage(content=(
                "Bạn là Destination Agent. Phân tích toàn bộ yêu cầu và hồ sơ nguồn để đánh giá từng ứng viên. "
                "Chỉ dùng ID được cung cấp; không tạo địa điểm, địa chỉ hoặc sự kiện mới. "
                "Điểm được nêu cụ thể là ràng buộc bắt buộc, có ưu tiên cao hơn sở thích nhóm. "
                "Có điểm bắt buộc KHÔNG có nghĩa chỉ được đi đúng một điểm đó. "
                "Đánh giá cả điểm bổ sung hợp tuyến, gần điểm bắt buộc, cùng trải nghiệm hoặc phù hợp sở thích. "
                "Dùng khoảng cách đường chim bay được tính sẵn để so sánh tương đối, không coi đó là đường bộ. "
                "Không đề xuất điểm xa nếu có điểm gần phù hợp hơn; không tự thêm sở thích người dùng. "
                "identity_matches đã xác định ứng viên nào là đúng điểm bắt buộc; không tự thay kết quả định danh. "
                "Cùng huyện hoặc nằm trong một khu vực KHÔNG có nghĩa là cùng địa điểm. "
                "Không dùng một điểm khác trong cùng huyện để thay thế địa điểm được gọi tên. "
                "Đánh dấu excluded nếu người dùng muốn tránh chính ứng viên đó. "
                "Chấm score 0..100 về mức phù hợp; reason là lý do ngắn bằng tiếng Việt dựa trên nguồn. "
                "Điểm ít liên quan phải có score dưới 40 và suitable=false. Không cố lấp đầy danh sách. "
                "reason phải giúp du khách hiểu lựa chọn; không nhắc ID, identity_matches hoặc tên trường kỹ thuật. "
                'Trả JSON {"places":[{"id":"ID", "score":90, "reason":"...", "suitable":true, "excluded":false}]}.'
            )),
            HumanMessage(content=json.dumps(payload, ensure_ascii=False)),
        ])
        data = extract_json_object(response.content)
        valid_ids = {p["id"] for p in batch}
        if not isinstance(data.get("places"), list):
            raise ValueError("Destination Agent không trả về danh sách đánh giá hợp lệ.")
        for judgment in data["places"]:
            if isinstance(judgment, dict) and judgment.get("id") in valid_ids:
                judgments[judgment["id"]] = judgment
        if not valid_ids <= judgments.keys():
            raise ValueError("Destination Agent chưa đánh giá đủ hồ sơ nguồn; vui lòng thử lại.")

    ranked = []
    for place in candidates:
        judgment = judgments[place["id"]]
        # The model ranks relevance; source-name identity decides which exact
        # venue satisfies a hard requirement. Nearby venues cannot substitute it.
        place["required_for"] = required_for(place, intent)
        if judgment.get("excluded") is True and not place["required_for"]:
            continue
        place["recommendation_reason"] = str(judgment.get("reason", ""))[:400]
        score = judgment.get("score", 0)
        score = float(score) if isinstance(score, (int, float)) else 0
        score = max(0, min(100, score)) if math.isfinite(score) else 0
        if not place["required_for"] and (score < 40 or judgment.get("suitable") is False):
            continue
        ranked.append((place, score))
    ranked.sort(key=lambda item: (not bool(item[0]["required_for"]), -item[1], normalized_name(item[0]["name"])))
    # Named places are never dropped just because the display limit was reached.
    required_count = sum(bool(p["required_for"]) for p, _ in ranked)
    return [p for p, _ in ranked[:max(limit, required_count)]]
