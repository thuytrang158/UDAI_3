"""
Phase 10: Master End-to-End Orchestrator for the AI Travel Planner.
Connects all agents, tools, and human-in-the-loop workflows into one LangGraph state machine.
"""
import sys
from langgraph.graph import StateGraph, START, END

# State & Schemas
from src.state import TripPlannerState
from src.schemas import Place

# Tools
from src.tools.places import search_places_osm, retry_missing_coordinates, get_places_notice
from src.tools.routing import calculate_route
from src.tools.clustering import group_places_by_days
from src.tools.accommodation import search_accommodations
from src.tools.cost_calculator import calculate_trip_cost
from src.tools.currency import INR_TO_VND_RATE, inr_to_vnd, vnd_to_inr
from src.tools.modification import modify_selection_with_llm
from src.tools.requirements import extract_trip_requirements
from src.tools.intent import validate_selection


# ======================================================================
# Observability Logging Helper (Requirement #24 & #25)
# ======================================================================
def log_step(badge: str, message: str):
    print(f"\n{badge} {message}")


# ======================================================================
# Node 1: Requirements Agent (Conversational Collection)
# ======================================================================
def requirements_agent_node(state: TripPlannerState) -> dict:
    log_step(" [Agent: TripRequirementsAgent]", "Collecting travel specifications...")

    # If requirements are already collected, skip prompt
    if (
        state.get("destination")
        and state.get("number_of_days")
        and state.get("number_of_travelers")
        and state.get("budget_per_day")
        and state.get("transportation_preference")
    ):
        return {}

    print("\n" + "=" * 68)
    print("       AI TRAVEL PLANNER - TRIP REQUIREMENTS GATHERING")
    print("=" * 68)

    dest_input = input("\nWhere would you like to travel? (default: Bengaluru): ").strip()
    dest = dest_input or "Bengaluru"

    days_input = input("How many days will your trip last? (default: 3): ").strip()
    try:
        days = int("".join(filter(str.isdigit, days_input))) or 3
    except ValueError:
        days = 3

    trav_input = input("How many people are traveling? (default: 2): ").strip()
    try:
        travelers = int("".join(filter(str.isdigit, trav_input))) or 2
    except ValueError:
        travelers = 2

    budget_input = input("Ngân sách mỗi người mỗi ngày bằng VND? (mặc định: 1.085.000 VND/ngày): ").strip()
    budget = budget_input or "1.085.000 VND/ngày"

    trans_input = input("Preferred transportation? (default: Cab and Metro): ").strip()
    transport = trans_input or "Cab and Metro"
    description = input("Mô tả thêm điểm bắt buộc, điểm muốn tránh hoặc sở thích (có thể bỏ trống): ").strip()

    # Preserve the conversational collection flow, then let the Requirements Agent
    # extract and validate the answers with the configured LLM + Pydantic schema.
    answers = (
        f"Destination: {dest}\nTrip duration: {days_input or str(days)}\nTravelers: {trav_input or str(travelers)}\n"
        f"Budget per person per day: {budget}\nTransportation preference: {transport}\nAdditional request: {description}"
    )
    try:
        extracted = extract_trip_requirements(answers)
        dest = extracted.get("destination", dest)
        days = extracted.get("number_of_days", days)
        travelers = extracted.get("number_of_travelers", travelers)
        budget = extracted.get("budget_per_day", budget)
        transport = extracted.get("transportation_preference", transport)
    except Exception as error:
        raise RuntimeError("Requirements Agent không gọi được AI hoặc nhận kết quả không hợp lệ. Kiểm tra model và thử lại.") from error

    print(f"\n Requirements confirmed for {dest} ({days} days, {travelers} travelers).")

    return {
        "destination": dest,
        "number_of_days": days,
        "number_of_travelers": travelers,
        "budget_per_day": budget,
        "transportation_preference": transport,
        "interests": extracted.get("interests", state.get("interests", [])),
        "trip_requirements": {**extracted, "user_request": description},
    }


# ======================================================================
# Node 2: Destination Agent (Discovers Top 10 Attractions)
# ======================================================================
def destination_agent_node(state: TripPlannerState) -> dict:
    dest = state.get("destination", "Bengaluru")
    log_step(" [Agent: DestinationAgent]", f"Invoking places discovery tool for '{dest}'...")

    raw_places = search_places_osm(dest, limit=10, interests=state.get("interests", []),
                                  trip_requirements=state.get("trip_requirements") or None)
    log_step("  [Tool: places.py]", f"Retrieved {len(raw_places)} curated locations.")
    if get_places_notice():
        print(f"  [Nguồn địa điểm] {get_places_notice()}")

    verified = []
    for p in raw_places:
        try:
            verified.append(Place(**p).model_dump())
        except Exception:
            pass

    return {"available_places": verified}


# ======================================================================
# Node 3: User Place Selection (Human-in-the-Loop Requirement #9)
# ======================================================================
def place_selection_node(state: TripPlannerState) -> dict:
    places = state.get("available_places", [])
    dest = state.get("destination", "Bengaluru")

    # If places are already selected and we aren't restarting, proceed
    if state.get("selected_places") and state.get("approval_status") != "START_OVER":
        return {}

    print("\n" + "=" * 68)
    print(f"       TOP 10 CURATED ATTRACTIONS IN {dest.upper()}")
    print("=" * 68)

    for idx, p in enumerate(places, start=1):
        print(f"\n[{idx}] {p['name']}")
        print(f"     Category    :   {p['category']}")
        print(f"     Description : {p['description']}")
        print(f"     Source      : {p.get('sources', [{}])[0].get('url', 'unknown')}")

    print("\n" + "-" * 68)
    print("Select 3 to 5 places you would like to visit.")
    print("Enter numbers separated by commas (e.g. 1, 5, 7, 10), or press Enter for default:")

    choice = input("Your selection: ").strip()
    if choice:
        try:
            indices = [int(x.strip()) - 1 for x in choice.split(",") if x.strip().isdigit()]
            selected = [places[i] for i in indices if 0 <= i < len(places)]
        except Exception:
            selected = []
    else:
        selected = places[:4]

    if not selected:
        selected = places[:1]
    for place in places:
        if place.get("required_for") and place not in selected:
            selected.append(place)
    validate_selection(selected, state.get("trip_requirements", {}))
    if not selected:
        print("Không có địa điểm phù hợp trong nguồn để lập lịch trình.")
    selected = retry_missing_coordinates(selected, state.get("destination", ""))
    for p in selected:
        if p.get("geocoding_status") != "source_coordinates" and (p.get("latitude") is None or p.get("longitude") is None):
            if p.get("geocoding_status") == "service_error":
                message = "Dịch vụ Nominatim từ chối truy cập" if p.get("geocoding_reason") == "access_forbidden" else "Dịch vụ tọa độ tạm thời không phản hồi"
            elif p.get("geocoding_status") in {"ambiguous", "rejected"}:
                message = "Cần xác minh địa điểm"
            else:
                message = "Chưa tìm thấy tọa độ"
            print(f"  {message}: {p['name']} — sẽ không ước tính quãng đường cho chặng liên quan.")

    log_step(" [Human-in-the-Loop]", f"Selected {len(selected)} places.")
    return {"selected_places": selected, "approval_status": "PENDING"}


# ======================================================================
# Node 4: Routing Tool (OSRM Road Matrix)
# ======================================================================
def routing_node(state: TripPlannerState) -> dict:
    places = retry_missing_coordinates(state.get("selected_places", []), state.get("destination", ""))
    log_step("  [Tool: routing.py (OSRM)]", f"Calculating driving routes for {len(places)} locations...")

    routes = []
    for i in range(len(places) - 1):
        p1 = places[i]
        p2 = places[i + 1]
        if any(p.get(k) is None for p in (p1, p2) for k in ("latitude", "longitude")):
            continue
        route_data = calculate_route(
            origin_lat=p1["latitude"], origin_lon=p1["longitude"],
            dest_lat=p2["latitude"], dest_lon=p2["longitude"]
        )
        routes.append({
            "origin_name": p1["name"],
            "destination_name": p2["name"],
            "distance_km": route_data["distance_km"],
            "duration_minutes": route_data["duration_minutes"],
            "source": route_data["source"]
        })

    return {"selected_places": places, "routes": routes}


# ======================================================================
# Node 5: Itinerary Agent (Day-by-Day Timetable)
# ======================================================================
def itinerary_agent_node(state: TripPlannerState) -> dict:
    dest = state.get("destination", "Bengaluru")
    days_count = state.get("number_of_days", 3)
    places = retry_missing_coordinates(state.get("selected_places", []), dest)
    transport = state.get("transportation_preference", "Cab and Metro")

    log_step("  [Agent: ItineraryAgent]", f"Generating timetable across {days_count} days...")

    day_buckets = group_places_by_days(places, days_count)
    itinerary_days = []

    for day_num, day_places in enumerate(day_buckets, start=1):
        schedule = []
        has_trek = any("Trek" in p.get("category", "") or "Hills" in p.get("name", "") for p in day_places)

        start_time = "05:30 AM" if has_trek else "09:00 AM"
        theme = "Scenic Excursion & Hilltop Trek" if has_trek else "Heritage & City Garden Discovery"

        schedule.append({
            "time": start_time,
            "activity": "Depart Hotel / Base",
            "details": f"Head out via {transport}."
        })

        current_hour = 6 if has_trek else 9
        minute_str = "30"

        for idx, place in enumerate(day_places):
            if idx > 0:
                prev = day_places[idx - 1]
                has_coordinates = all(p.get(k) is not None for p in (prev, place) for k in ("latitude", "longitude"))
                route = calculate_route(prev["latitude"], prev["longitude"], place["latitude"], place["longitude"]) if has_coordinates else None
                schedule.append({
                    "time": f"{current_hour:02d}:{minute_str}",
                    "activity": f"Travel to {place['name']}",
                    "details": f"Drive: {route['distance_km']} km | ~{route['duration_minutes']} mins via {transport}." if route else "Chưa có đủ tọa độ; chưa thể ước tính quãng đường và thời gian di chuyển."
                })
                if route:
                    current_hour += (route["duration_minutes"] // 60)

            schedule.append({
                "time": f"{current_hour:02d}:{minute_str}",
                "activity": place["name"],
                "details": f"Category: {place['category']} — {place['description']}" + (" (chưa xác định được tọa độ)" if place.get("latitude") is None else ""),
                "place_id": place.get("id"), "sources": place.get("sources", []),
                "geocoding_status": place.get("geocoding_status", "unavailable"),
                "geocoding_reason": place.get("geocoding_reason"),
                "coordinate_source": place.get("coordinate_source"),
                "coordinate_reference_url": place.get("coordinate_reference_url"),
                "coordinate_attribution": place.get("coordinate_attribution")
            })
            current_hour += 2

            if current_hour in [12, 13, 14] and not any("Lunch" in it["activity"] for it in schedule):
                schedule.append({
                    "time": "01:30 PM",
                    "activity": "Lunch & Rest Break",
                    "details": "Local cuisine tasting and relaxation."
                })
                current_hour += 1

        schedule.append({
            "time": "06:00 PM",
            "activity": "Return to Accommodation",
            "details": "Free leisure evening."
        })

        itinerary_days.append({
            "day_number": day_num,
            "theme": theme,
            "schedule": schedule
        })

    return {
        "selected_places": places,
        "itinerary": {
            "destination": dest,
            "total_days": days_count,
            "days": itinerary_days
        }
    }


def _coordinate_status_message(activity: dict) -> str | None:
    status = activity.get("geocoding_status")
    if not activity.get("place_id") or status in {"source_coordinates", "nominatim_verified", "reference_coordinates"}:
        return None
    messages = {
        "configuration_error": "Chưa cấu hình dịch vụ tọa độ.",
        "service_error": "Dịch vụ tọa độ tạm thời không phản hồi.",
        "ambiguous": "Có nhiều kết quả tọa độ khó phân biệt; cần xác minh.",
        "rejected": "Kết quả tọa độ không khớp địa điểm hoặc khu vực.",
        "not_found": "Không tìm thấy tọa độ phù hợp.",
    }
    if status == "service_error" and activity.get("geocoding_reason") == "access_forbidden":
        return "Dịch vụ Nominatim từ chối truy cập."
    return messages.get(status, "Chưa xác định được tọa độ.")


# ======================================================================
# Node 6: Human Approval Gate (Requirement #10 & #11)
# ======================================================================
def human_itinerary_gate_node(state: TripPlannerState) -> dict:
    itin = state.get("itinerary", {})

    print("\n" + "=" * 68)
    print(f"       PROPOSED {itin.get('total_days')}-DAY ITINERARY FOR {itin.get('destination').upper()}")
    print("=" * 68)

    for d in itin.get("days", []):
        print(f"\n DAY {d['day_number']}: {d['theme']}")
        print("-" * 68)
        for item in d["schedule"]:
            print(f"  • {item['time']:<10} | {item['activity']}")
            print(f"    {'':<10}   └── {item['details']}")
            status_message = _coordinate_status_message(item)
            if status_message:
                print(f"    {'':<10}      Trạng thái tọa độ: {status_message}")
            if item.get("coordinate_source") == "Nominatim":
                attribution = item.get("coordinate_attribution")
                print(f"    {'':<10}      Nguồn tọa độ: Nominatim / OpenStreetMap" + (f" · {attribution}" if attribution else ""))

    print("\n" + "=" * 68)
    print("HUMAN APPROVAL REQUIRED:")
    print("  [1] Accept (Proceed to Accommodation)")
    print("  [2] Modify (Swap an attraction)")
    print("  [3] Start Over (Re-select attractions)")
    print("=" * 68)

    while True:
        choice = input("Your choice (1, 2, or 3, default=1): ").strip() or "1"
        if choice in ["1", "2", "3"]:
            break

    if choice == "1":
        log_step(" [Human Gate]", "Itinerary ACCEPTED.")
        return {"approval_status": "ACCEPTED", "itinerary_approved": True}
    elif choice == "2":
        fb = input("What would you like to change? (e.g. 'replace Bangalore Palace with Turahalli Forest'): ").strip()
        log_step(" [Human Gate]", f"Modification requested: '{fb}'")
        return {"approval_status": "MODIFY", "user_feedback": fb, "itinerary_approved": False}
    else:
        log_step(" [Human Gate]", "Resetting attractions...")
        return {"approval_status": "START_OVER", "itinerary_approved": False}


# ======================================================================
# Node 7: Handle Modification / Re-selection
# ======================================================================
def handle_modification_node(state: TripPlannerState) -> dict:
    feedback = state.get("user_feedback") or ""
    selected = state.get("selected_places", [])
    available = state.get("available_places", [])

    updated_selected = modify_selection_with_llm(
        feedback=feedback,
        selected_places=selected,
        available_places=available,
        trip_requirements=state.get("trip_requirements", {})
    )
    validate_selection(updated_selected, state.get("trip_requirements", {}))

    log_step(" [Graph Cycle]", f"Updated itinerary selections to {len(updated_selected)} places based on feedback.")
    return {"selected_places": updated_selected, "approval_status": "PENDING"}

# ======================================================================
# Node 8: Stay Agent (Accommodation Selection)
# ======================================================================
def stay_agent_node(state: TripPlannerState) -> dict:
    log_step(" [Agent: StayAgent]", "Gathering accommodation preferences...")

    print("\n" + "=" * 68)
    print("      ACCOMMODATION PREFERENCES (STAY AGENT)")
    print("=" * 68)

    print("\nWhat type of accommodation would you prefer?")
    print("  [1] Hotel  [2] Hostel  [3] Apartment  [4] No preference")
    t_map = {"1": "Hotel", "2": "Hostel", "3": "Apartment", "4": "No preference", "hotel": "Hotel", "hostel": "Hostel"}
    t_in = input("Select type (1-4, default=1): ").strip().lower() or "1"
    chosen_type = t_map.get(t_in, "Hotel")

    b_in = input("Ngân sách tối đa mỗi đêm bằng VND? (mặc định=1.356.860): ").strip() or "1356860"
    try:
        budget_vnd = int("".join(filter(str.isdigit, b_in))) or 1356860
        budget = vnd_to_inr(budget_vnd)
    except ValueError:
        budget = 5000

    print("\nWhich location would you prefer?")
    print("  [1] City Center  [2] Near Public Transport  [3] Quiet Area  [4] No preference")
    a_map = {"1": "City Center", "2": "Near Public Transport", "3": "Quiet Area", "4": "No preference"}
    a_in = input("Select area (1-4, default=4): ").strip() or "4"
    chosen_area = a_map.get(a_in, "No preference")

    # Call accommodation tool
    log_step("  [Tool: accommodation.py]", f"Tìm {chosen_type} dưới {inr_to_vnd(budget):,} VND tại {chosen_area}...")
    options = search_accommodations(
        destination=state.get("destination", "Bengaluru"),
        stay_type=chosen_type,
        max_budget=budget,
        preferred_area=chosen_area,
        trip_context={"requirements": state.get("trip_requirements", {}),
                       "selected_places": [{"name": p.get("name"), "address": p.get("address")} for p in state.get("selected_places", [])]}
    )

    print("\n" + "=" * 68)
    print("           RECOMMENDED ACCOMMODATION OPTIONS")
    print("=" * 68)

    for idx, opt in enumerate(options, start=1):
        print(f"\n[{idx}] {opt['name']} ({opt['stay_type']})")
        print(f"     • Area      : {opt['area_type']}")
        print(f"     • Giá       : {inr_to_vnd(opt['price_per_night']):,} VND / đêm")
        print(f"     • Rating    : ⭐ {opt['rating']} / 5.0")
        print(f"     • Booking   : {opt['booking_url']}")
        print(f"     • Note      : {opt['disclaimer']}")

    print("\n" + "-" * 68)
    while True:
        sel = input(f"Select your accommodation (1-{len(options)}, default=1): ").strip() or "1"
        if sel.isdigit() and 1 <= int(sel) <= len(options):
            selected_stay = options[int(sel) - 1]
            break

    log_step(" [Human-in-the-Loop]", f"Selected stay: {selected_stay['name']}")
    return {"selected_accommodation": selected_stay}


# ======================================================================
# Node 9: Cost Calculator Tool (Deterministic Arithmetic)
# ======================================================================
def cost_calculator_node(state: TripPlannerState) -> dict:
    log_step(" [Tool: cost_calculator.py]", "Computing exact trip expenses in Python...")

    days = state.get("number_of_days", 3)
    travelers = state.get("number_of_travelers", 2)
    stay = state.get("selected_accommodation", {})
    nightly_rate = stay.get("price_per_night", 2200)
    routes = state.get("routes", [])
    transport = state.get("transportation_preference", "Cab and Metro")

    cost_data = calculate_trip_cost(
        number_of_days=days,
        number_of_travelers=travelers,
        nightly_rate=nightly_rate,
        routes=routes,
        transport_pref=transport
    )

    for key in ("accommodation_cost", "transportation_cost", "food_cost", "activities_cost", "miscellaneous_cost", "total_estimated_cost"):
        cost_data[key] = inr_to_vnd(cost_data[key])
    cost_data["currency"] = "VND"
    cost_data["exchange_rate_inr_to_vnd"] = INR_TO_VND_RATE
    cost_data["breakdown_notes"]["rate_per_km"] = inr_to_vnd(cost_data["breakdown_notes"]["rate_per_km"])

    log_step(" [Tool: cost_calculator.py]", f"Tổng dự kiến: {cost_data['total_estimated_cost']:,} VND")
    return {"estimated_cost": cost_data}


# ======================================================================
# Node 10: Final Planner Agent (Compiles Master Package)
# ======================================================================
def final_planner_node(state: TripPlannerState) -> dict:
    log_step(" [Agent: FinalPlannerAgent]", "Assembling Master Trip Dossier...")

    dest = state.get("destination", "Bengaluru")
    days = state.get("number_of_days", 3)
    travelers = state.get("number_of_travelers", 2)
    stay = state.get("selected_accommodation", {})
    costs = state.get("estimated_cost", {})
    itin = state.get("itinerary", {})
    nights = max(days - 1, 1)

    print("\n" + "#" * 72)
    print(f"        MASTER TRIP ITINERARY DOSSIER: {dest.upper()}")
    print("#" * 72)

    print(f"\nTRIP OVERVIEW:")
    print(f" • Destination        : {dest}")
    print(f" • Duration           : {days} Days / {nights} Nights")
    print(f" • Travelers          : {travelers} Persons")
    print(f" • Transportation     : {state.get('transportation_preference')}")

    print(f"\nACCOMMODATION DETAILS:")
    print(f" • Property           : {stay.get('name')}")
    print(f" • Type & Location    : {stay.get('stay_type')} ({stay.get('area_type')})")
    print(f" • Giá                : {inr_to_vnd(stay.get('price_per_night', 0)):,} VND / đêm")
    print(f" • External Booking   : {stay.get('booking_url')}")
    print(f" • Status Note        : {stay.get('disclaimer')}")

    print(f"\nDAY-BY-DAY SCHEDULE:")
    for d in itin.get("days", []):
        print(f"\n   DAY {d['day_number']}: {d['theme']}")
        print(f"  {'-' * 68}")
        for item in d.get("schedule", []):
            print(f"    • {item['time']:<10} | {item['activity']}")
            print(f"      {'':<10}   └── {item['details']}")
            status_message = _coordinate_status_message(item)
            if status_message:
                print(f"      {'':<10}      Trạng thái tọa độ: {status_message}")
            if item.get("coordinate_source") == "Nominatim":
                attribution = item.get("coordinate_attribution")
                print(f"      {'':<10}      Nguồn tọa độ: Nominatim / OpenStreetMap" + (f" · {attribution}" if attribution else ""))

    print(f"\nCOST BREAKDOWN (DETERMINISTIC PYTHON CALCULATION):")
    print(f"  --------------------------------------------------------------")
    print(f"  Chi phí chỗ ở ({nights} đêm)        : {costs.get('accommodation_cost', 0):,} VND")
    print(f"  Di chuyển                         : {costs.get('transportation_cost', 0):,} VND")
    print(f"  Ăn uống                            : {costs.get('food_cost', 0):,} VND")
    print(f"  Hoạt động và vé                    : {costs.get('activities_cost', 0):,} VND")
    print(f"  Dự phòng                           : {costs.get('miscellaneous_cost', 0):,} VND")
    print(f"  --------------------------------------------------------------")
    print(f"  TỔNG CHI PHÍ DỰ KIẾN               : {costs.get('total_estimated_cost', 0):,} VND")
    print(f"  --------------------------------------------------------------")

    print("\n" + "#" * 72)
    print(" All trip objectives fulfilled! System ready for Phase 11 (FastAPI + Web UI).")
    print("#" * 72 + "\n")

    return {"final_trip_summary": {"status": "COMPLETE", "selected_places": state.get("selected_places", [])}}


# ======================================================================
# Conditional Edge Router
# ======================================================================
def route_approval(state: TripPlannerState) -> str:
    status = state.get("approval_status")
    if status == "ACCEPTED":
        return "stay_agent"
    elif status == "MODIFY":
        return "handle_modification"
    else:
        return "place_selection"


# ======================================================================
# Master Graph Construction
# ======================================================================
def build_master_travel_graph():
    workflow = StateGraph(TripPlannerState)

    # 1. Register all nodes
    workflow.add_node("requirements", requirements_agent_node)
    workflow.add_node("destination", destination_agent_node)
    workflow.add_node("place_selection", place_selection_node)
    workflow.add_node("routing", routing_node)
    workflow.add_node("itinerary", itinerary_agent_node)
    workflow.add_node("human_gate", human_itinerary_gate_node)
    workflow.add_node("handle_modification", handle_modification_node)
    workflow.add_node("stay_agent", stay_agent_node)
    workflow.add_node("cost_calculator", cost_calculator_node)
    workflow.add_node("final_planner", final_planner_node)

    # 2. Add linear flow edges
    workflow.add_edge(START, "requirements")
    workflow.add_edge("requirements", "destination")
    workflow.add_edge("destination", "place_selection")
    workflow.add_edge("place_selection", "routing")
    workflow.add_edge("routing", "itinerary")
    workflow.add_edge("itinerary", "human_gate")

    # 3. Add conditional edge for human approval
    workflow.add_conditional_edges(
        "human_gate",
        route_approval,
        {
            "stay_agent": "stay_agent",
            "handle_modification": "handle_modification",
            "place_selection": "place_selection",
        }
    )

    # 4. Cycles (Loop-backs on modify)
    workflow.add_edge("handle_modification", "routing")

    # 5. Final stretch
    workflow.add_edge("stay_agent", "cost_calculator")
    workflow.add_edge("cost_calculator", "final_planner")
    workflow.add_edge("final_planner", END)

    return workflow.compile()


# ======================================================================
# Execution Entry Point
# ======================================================================
if __name__ == "__main__":
    app = build_master_travel_graph()

    initial_state: TripPlannerState = {
        "messages": [],
        "destination": None,
        "number_of_days": None,
        "number_of_travelers": None,
        "budget_per_day": None,
        "transportation_preference": None,
        "available_places": [],
        "selected_places": [],
        "routes": [],
        "itinerary": {},
        "itinerary_approved": False,
        "approval_status": "PENDING",
        "user_feedback": None,
        "accommodation_preferences": {},
        "accommodation_options": [],
        "selected_accommodation": {},
        "estimated_cost": {},
        "final_trip_summary": {},
    }

    try:
        app.invoke(initial_state)
    except (KeyboardInterrupt, EOFError):
        print("\n\nSession terminated by user.")
        sys.exit(0)
