"""
Phase 11: FastAPI Backend API for AI Travel Planner.
Exposes multi-agent workflows as structured REST endpoints.
"""
import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, ValidationError

# Tools & Schemas
from src.tools.places import search_places_osm, retry_missing_coordinates, get_places_notice
from src.tools.routing import calculate_route
from src.tools.clustering import group_places_by_days
from src.tools.accommodation import search_accommodations
from src.tools.cost_calculator import calculate_trip_cost
from src.tools.modification import modify_selection_with_llm
from src.tools.requirements import extract_trip_requirements, RequirementsOutputError, requirements_model_info
from src.schemas import ExtractedTripRequirements, Interest
from src.tools.intent import requirement_report, validate_selection
from src.tools.currency import INR_TO_VND_RATE, inr_to_vnd, vnd_to_inr
from src.rag_retrieval import initialize_rag_index, rag_index_health, retrieve_rag_chunks


app = FastAPI(
    title="AI Travel Planner API",
    version="1.0.0",
    description="Multi-Agent Open-Source AI Travel Planner"
)


@app.on_event("startup")
def warm_bge_m3_rag_index():
    """Load BGE-M3 and prepare/reuse the persistent knowledge-base index."""
    try:
        status = initialize_rag_index()
        print(f"BGE-M3 RAG ready: {status['chunk_count']} chunks in Qdrant local store.")
    except Exception as error:
        # Keep Planner routes available; /api/rag/retrieve will retry and report 503.
        print(f"BGE-M3 RAG initialization deferred: {type(error).__name__}: {error}")

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static folder for web UI
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")


# ----------------------------------------------------------------------
# Request / Response Schemas
# ----------------------------------------------------------------------
class RequirementsRequest(BaseModel):
    destination: str = Field(default="Bengaluru", min_length=2, max_length=200)
    number_of_days: int = Field(default=3, ge=1, le=30)
    number_of_travelers: int = Field(default=2, ge=1)
    budget_per_day: str = "1.085.000 VND/ngày"
    transportation_preference: str = "Cab and Metro"
    interests: List[Interest] = Field(default_factory=list)
    request_text: str = Field(default="", max_length=4000)


class PlanningContext(BaseModel):
    trip_requirements: dict = Field(default_factory=dict)


class GenerateItineraryRequest(PlanningContext):
    destination: str
    number_of_days: int
    transportation_preference: str
    selected_places: List[dict]


class ModifyItineraryRequest(PlanningContext):
    feedback: str
    available_places: List[dict]
    selected_places: List[dict]
    destination: str = "Bengaluru"
    number_of_days: int = 3
    transportation_preference: str = "Cab and Metro"


class SearchStaysRequest(PlanningContext):
    destination: str
    stay_type: str = "Hotel"
    max_budget: int = 1356850
    preferred_area: str = "Quiet Area"
    selected_places: List[dict] = Field(default_factory=list)


class FinalizeTripRequest(PlanningContext):
    destination: str
    number_of_days: int
    number_of_travelers: int
    transportation_preference: str
    itinerary: dict
    selected_accommodation: dict
    routes: List[dict]
    selected_places: List[dict] = Field(default_factory=list)


class RagRetrieveRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1200)
    limit: int = Field(default=12, ge=1, le=30)


# ----------------------------------------------------------------------
# API Endpoints
# ----------------------------------------------------------------------
@app.get("/")
def serve_ui():
    """Serves the single-page application UI."""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "AI Travel Planner API running. Place index.html in src/static/."}


@app.get("/api/rag/health")
def rag_health():
    return rag_index_health()


@app.post("/api/rag/retrieve")
def retrieve_rag(req: RagRetrieveRequest):
    try:
        return retrieve_rag_chunks(req.query.strip(), req.limit)
    except Exception as error:
        print(f"BGE-M3 RAG retrieval failed: {type(error).__name__}: {error}")
        raise HTTPException(
            status_code=503,
            detail="BGE-M3 RAG chưa sẵn sàng. Kiểm tra log FastAPI và kết nối tải model.",
        ) from error


@app.post("/api/trip/initiate")
def initiate_trip(req: RequirementsRequest):
    """
    Step 1: Discovers Top attractions tailored to destination AND travel interests.
    """
    requirements = {
        "destination": req.destination,
        "number_of_days": req.number_of_days,
        "number_of_travelers": req.number_of_travelers,
        "budget_per_day": req.budget_per_day,
        "transportation_preference": req.transportation_preference,
        "interests": list(req.interests),
        "required_places": [], "excluded_places": [], "preferences": [], "pace": "balanced",
    }
    agent = {**requirements_model_info(), "status": "not_requested"}
    if req.request_text.strip():
        try:
            extracted = extract_trip_requirements(req.request_text.strip(), context=requirements)
            # Keep explicitly selected categories alongside interests found in the description.
            extracted["interests"] = list(dict.fromkeys(req.interests + extracted.get("interests", [])))
            requirements.update(extracted)
            agent["status"] = "completed"
        except RequirementsOutputError as error:
            raise HTTPException(status_code=422, detail=(
                "AI chưa phân tích được mô tả thành thông tin hợp lệ. "
                "Hãy ghi rõ điểm đến, số ngày và số người rồi thử lại."
            )) from error
        except Exception as error:
            print(f"Requirements Agent failed: {type(error).__name__}")
            raise HTTPException(status_code=503, detail=(
                f"Không gọi được model {agent['model']} qua {agent['provider']}. "
                "Kiểm tra kết nối hoặc cấu hình model rồi thử lại; mô tả của bạn vẫn được giữ trên trang."
            )) from error

    try:
        requirements = ExtractedTripRequirements.model_validate(requirements).model_dump(exclude_none=True)
    except ValidationError as error:
        raise HTTPException(status_code=422, detail="Thông tin chuyến đi không hợp lệ. Vui lòng kiểm tra lại biểu mẫu.") from error
    if any(not requirements.get(key) for key in (
        "destination", "number_of_days", "number_of_travelers", "budget_per_day", "transportation_preference"
    )):
        raise HTTPException(status_code=422, detail="Vui lòng điền đủ điểm đến, số ngày, số người, ngân sách và phương tiện.")

    dest = requirements["destination"].strip()
    intent = {**requirements, "user_request": req.request_text.strip()}
    discovery_args = {"limit": 10, "interests": requirements["interests"]}
    if req.request_text.strip():
        discovery_args["trip_requirements"] = intent
    try:
        places = search_places_osm(dest, **discovery_args)
    except Exception as error:
        print(f"Destination Agent failed: {type(error).__name__}")
        raise HTTPException(status_code=503, detail=(
            "Destination Agent chưa đánh giá được địa điểm theo mô tả. "
            "Vui lòng thử lại; yêu cầu của bạn vẫn được giữ nguyên."
        )) from error

    return {
        "destination": dest,
        "number_of_days": requirements["number_of_days"],
        "number_of_travelers": requirements["number_of_travelers"],
        "budget_per_day": requirements["budget_per_day"],
        "transportation_preference": requirements["transportation_preference"],
        "interests": requirements["interests"],
        "requirements_agent": agent,
        "trip_requirements": intent,
        "requirement_report": requirement_report(places, intent),
        "available_places": places,
        "places_notice": get_places_notice() or ("" if places else "Không tìm thấy địa điểm phù hợp lúc này. Một hoặc nhiều nguồn dữ liệu có thể đang tạm thời không truy cập được."),
        "status": "PLACES_DISCOVERED" if places else "NO_PLACES_FOUND"
    }


@app.post("/api/trip/generate-itinerary")
def generate_itinerary(req: GenerateItineraryRequest):
    """
    Steps 2 & 3: Calculates OSRM routes, clusters stops, and builds the timetable.
    """
    check_trip_constraints(req.selected_places, req.trip_requirements, req.number_of_days)
    places = retry_missing_coordinates(req.selected_places, req.destination)
    if not places:
        raise HTTPException(status_code=400, detail="Vui lòng chọn ít nhất một địa điểm tham quan.")
    itinerary = build_itinerary(places, req.number_of_days, req.transportation_preference, calculate_route, req.trip_requirements)
    routes = itinerary.pop("_routes", [])

    return {
        "selected_places": places,
        "routes": routes,
        "itinerary": {"destination": req.destination, "total_days": req.number_of_days, **itinerary},
        "trip_requirements": req.trip_requirements,
        "requirement_report": requirement_report(places, req.trip_requirements)
    }


@app.post("/api/trip/modify")
def modify_itinerary(req: ModifyItineraryRequest):
    """
    Human-in-the-Loop modification handler.
    """
    feedback = req.feedback.lower()
    if req.trip_requirements:
        selected = modify_selection_with_llm(req.feedback, req.selected_places, req.available_places,
                                              trip_requirements=req.trip_requirements)
    else:
        selected = modify_selection_with_llm(req.feedback, req.selected_places, req.available_places)
    available = req.available_places
    # Reject non-available IDs/names and locations without coordinates before routing.
    available_by_id = {p.get("id"): p for p in available if p.get("id")}
    if available_by_id:
        selected = [available_by_id[p.get("id")] for p in selected if p.get("id") in available_by_id]
    check_trip_constraints(selected, req.trip_requirements, req.number_of_days)
    selected = retry_missing_coordinates(selected, req.destination)
    # Rebuild routes and schedule from the accepted place selection so that the
    # itinerary shown to the user and later included in the dossier stay aligned.
    itinerary = build_itinerary(selected, req.number_of_days, req.transportation_preference, calculate_route, req.trip_requirements)
    routes = itinerary.pop("_routes", [])
    itinerary.update({"destination": req.destination, "total_days": req.number_of_days})
    return {"selected_places": selected, "itinerary": itinerary, "routes": routes,
            "trip_requirements": req.trip_requirements, "requirement_report": requirement_report(selected, req.trip_requirements)}


def check_trip_constraints(places, intent, number_of_days=None):
    try:
        validate_selection(places, intent)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    if number_of_days and intent:
        capacity = {"relaxed": 2, "balanced": 4, "active": 6}.get(intent.get("pace"), 4)
        if len(places) > number_of_days * capacity:
            raise HTTPException(status_code=409, detail=(
                f"Bạn đang chọn {len(places)} điểm cho {number_of_days} ngày. "
                f"Với nhịp độ đã yêu cầu, hãy chọn tối đa {number_of_days * capacity} điểm hoặc tăng số ngày ở bước 1."
            ))


def build_itinerary(places, number_of_days, transport_preference, route_calculator, trip_requirements=None):
    """Create a Vietnamese schedule while preserving existing place/category values."""
    day_buckets = group_places_by_days(places, number_of_days)
    itinerary_days = []
    route_legs = []
    for day_num, day_places in enumerate(day_buckets, start=1):
        schedule = []
        # Preserve the original English value checks used by existing place data.
        has_trek = any("Trek" in p.get("category", "") or "Hills" in p.get("name", "") for p in day_places)
        theme = "Khám phá thiên nhiên và trekking trên đồi" if has_trek else "Khám phá di sản và cảnh quan địa phương"
        if not day_places:
            theme = "Ngày tự do nghỉ ngơi và khám phá"
        schedule.append({
            "time": "05:30" if has_trek else "09:00",
            "activity": "Khởi hành từ nơi lưu trú",
            "details": f"Bắt đầu hành trình bằng {transport_preference}."
        })
        current_minutes = (6 if has_trek else 9) * 60 + 30
        visit_minutes = {"relaxed": 150, "balanced": 120, "active": 90}.get((trip_requirements or {}).get("pace"), 120)
        for idx, place in enumerate(day_places):
            if idx > 0:
                prev = day_places[idx - 1]
                has_route_coordinates = all(prev.get(key) is not None and place.get(key) is not None for key in ("latitude", "longitude"))
                if has_route_coordinates:
                    leg = route_calculator(prev["latitude"], prev["longitude"], place["latitude"], place["longitude"])
                    travel_details = f"Quãng đường {leg['distance_km']} km, thời gian dự kiến {leg['duration_minutes']} phút."
                    route_legs.append({
                        "day_number": day_num, "origin_name": prev["name"], "destination_name": place["name"],
                        "distance_km": leg["distance_km"], "duration_minutes": leg["duration_minutes"],
                        "source": leg.get("source", "route calculator")
                    })
                    departure_minutes = current_minutes
                    current_minutes += max(0, int(leg["duration_minutes"]))
                else:
                    departure_minutes = current_minutes
                    travel_details = "Chưa có đủ tọa độ để ước tính quãng đường và thời gian di chuyển."
                schedule.append({
                    "time": f"{departure_minutes // 60:02d}:{departure_minutes % 60:02d}",
                    "activity": f"Di chuyển đến {place['name']}",
                    "details": travel_details
                })
            category = place.get("category", "Địa điểm tham quan")
            category_labels = {
                "Trekking & Adventure": "Leo núi và phiêu lưu", "Parks & Leisure": "Công viên và thư giãn",
                "Heritage & Architecture": "Di sản và kiến trúc", "Spiritual & Wellness": "Tâm linh và chăm sóc sức khỏe",
                "Food & Culinary": "Ẩm thực", "Shopping & Bazaars": "Mua sắm và chợ truyền thống",
            }
            schedule.append({
                "time": f"{current_minutes // 60:02d}:{current_minutes % 60:02d}",
                "activity": place["name"],
                "details": f"{category_labels.get(category, category)} — {place.get('description', 'Chưa có nội dung giới thiệu trong nguồn.')}" + (" — Chưa xác định được tọa độ." if place.get("latitude") is None or place.get("longitude") is None else ""),
                "place_id": place.get("id"), "sources": place.get("sources", []),
                "geocoding_status": place.get("geocoding_status", "unavailable"),
                "geocoding_reason": place.get("geocoding_reason"),
                "coordinate_source": place.get("coordinate_source"),
                "coordinate_reference_url": place.get("coordinate_reference_url"),
                "coordinate_attribution": place.get("coordinate_attribution")
            })
            current_minutes += visit_minutes
            if current_minutes >= 12 * 60 and not any("Nghỉ trưa" in item["activity"] for item in schedule):
                schedule.append({"time": f"{current_minutes // 60:02d}:{current_minutes % 60:02d}", "activity": "Nghỉ trưa và dùng bữa", "details": "Thưởng thức ẩm thực địa phương và nghỉ ngơi."})
                current_minutes += 60
        if current_minutes > 21 * 60:
            raise HTTPException(status_code=409, detail=f"Ngày {day_num} quá dài theo thời gian di chuyển thực tế. Hãy giảm điểm hoặc tăng số ngày, giữ lại điểm bắt buộc.")
        return_minutes = max(18 * 60, current_minutes)
        schedule.append({"time": f"{return_minutes // 60:02d}:{return_minutes % 60:02d}", "activity": "Kết thúc tham quan; trở về nơi lưu trú", "details": "Giờ kết thúc các hoạt động dự kiến; thời gian về chỗ ở cần tính lại sau khi chọn nơi lưu trú."})
        itinerary_days.append({"day_number": day_num, "theme": theme, "schedule": schedule})
    return {"days": itinerary_days, "_routes": route_legs}


@app.post("/api/trip/stays")
def get_stays(req: SearchStaysRequest):
    """
    Step 4: Retrieves authentic properties filtered by user criteria.
    """
    check_trip_constraints(req.selected_places, req.trip_requirements)
    stay_args = {}
    if req.trip_requirements:
        stay_args["trip_context"] = {"requirements": req.trip_requirements,
                                    "selected_places": [{"name": p.get("name"), "address": p.get("address")} for p in req.selected_places]}
    try:
        options = search_accommodations(
            destination=req.destination,
            stay_type=req.stay_type,
            max_budget=vnd_to_inr(req.max_budget),
            preferred_area=req.preferred_area,
            **stay_args
        )
    except Exception as error:
        raise HTTPException(status_code=503, detail="Stay Agent chưa tìm được gợi ý bằng AI. Hãy thử lại hoặc điều chỉnh tiêu chí.") from error
    for option in options:
        option["price_per_night"] = inr_to_vnd(option.get("price_per_night", 0))
        option["currency"] = "VND"
    return {"accommodation_options": options}


@app.post("/api/trip/finalize")
def finalize_trip(req: FinalizeTripRequest):
    """
    Step 5: Calculates deterministic costs and compiles the Master Dossier.
    """
    check_trip_constraints(req.selected_places, req.trip_requirements, req.number_of_days)
    days = req.itinerary.get("days") if isinstance(req.itinerary, dict) else None
    if not isinstance(days, list) or len(days) != req.number_of_days or any(
        not isinstance(day, dict) or day.get("day_number") != index + 1
        or not isinstance(day.get("schedule"), list) or not day["schedule"]
        or any(not isinstance(item, dict) or not item.get("time") or not item.get("activity") or item.get("details") is None for item in day["schedule"])
        for index, day in enumerate(days)
    ):
        raise HTTPException(status_code=400, detail="Lịch trình chưa đầy đủ. Vui lòng quay lại bước Lịch trình để tạo và xác nhận lại.")
    if req.trip_requirements.get("required_places"):
        activities = [item for day in days for item in day["schedule"]]
        scheduled = [p for p in req.selected_places if any(
            (item.get("place_id") and item["place_id"] == p.get("id")) or item.get("activity") == p.get("name")
            for item in activities)]
        check_trip_constraints(scheduled, req.trip_requirements)
    stay = req.selected_accommodation
    # The stays API exposes VND amounts; cost assumptions remain internal INR.
    nightly_rate = vnd_to_inr(stay.get("price_per_night", inr_to_vnd(2200)))

    cost_data = calculate_trip_cost(
        number_of_days=req.number_of_days,
        number_of_travelers=req.number_of_travelers,
        nightly_rate=nightly_rate,
        routes=req.routes,
        transport_pref=req.transportation_preference
    )
    for key in ("accommodation_cost", "transportation_cost", "food_cost", "activities_cost", "miscellaneous_cost", "total_estimated_cost"):
        cost_data[key] = inr_to_vnd(cost_data[key])
    cost_data["currency"] = "VND"
    cost_data["exchange_rate_inr_to_vnd"] = INR_TO_VND_RATE
    cost_data["breakdown_notes"]["rate_per_km"] = inr_to_vnd(cost_data["breakdown_notes"]["rate_per_km"])
    stay["currency"] = "VND"

    return {
        "destination": req.destination,
        "duration_summary": f"{req.number_of_days} Days / {max(req.number_of_days - 1, 1)} Nights",
        "travelers": req.number_of_travelers,
        "selected_accommodation": stay,
        "selected_places": req.selected_places,
        "itinerary": req.itinerary,
        "cost_breakdown": cost_data,
        "exchange_rate_inr_to_vnd": INR_TO_VND_RATE,
        "status": "FINALIZED",
        "trip_requirements": req.trip_requirements,
        "requirement_report": requirement_report(req.selected_places, req.trip_requirements)
    }
