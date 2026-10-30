"""
Deterministic Trip Cost Calculator Tool.
Pure Python arithmetic — zero LLM hallucination.
"""
from typing import Dict, Any, List


def calculate_trip_cost(
    number_of_days: int,
    number_of_travelers: int,
    nightly_rate: int,
    routes: List[Dict[str, Any]],
    transport_pref: str = "Cab and Metro"
) -> Dict[str, Any]:
    """
    Calculates exact trip costs based on verified parameters.
    """
    # 1. Accommodation: (Days - 1) nights
    nights = max(number_of_days - 1, 1)
    accommodation_total = nightly_rate * nights

    # 2. Transportation: Sum up OSRM road distances
    total_km = sum(r.get("distance_km", 0.0) for r in routes)
    # Default minimum base travel if routes list is empty: ~25 km/day
    if total_km == 0:
        total_km = number_of_days * 25.0

    # Rate per km in INR based on transport mode
    lowered_pref = transport_pref.lower()
    if "metro" in lowered_pref and "cab" not in lowered_pref:
        rate_per_km = 8.0   # Public transit
    elif "cab" in lowered_pref or "taxi" in lowered_pref:
        rate_per_km = 18.0  # City cab rate
    else:
        rate_per_km = 15.0  # Mixed transit

    # Transit cost = base fare + (total km * rate)
    transit_total = int(300 + (total_km * rate_per_km))

    # 3. Food Cost: ~₹900 per person per day (Breakfast, Lunch, Dinner, Snacks)
    food_per_person_per_day = 900
    food_total = number_of_travelers * number_of_days * food_per_person_per_day

    # 4. Activities & Entry fees: ~₹400 per person for garden/monument entries
    activities_total = number_of_travelers * 400

    # 5. Miscellaneous buffer: ~₹500 per day
    misc_total = number_of_days * 500

    # Grand Total
    grand_total = (
        accommodation_total
        + transit_total
        + food_total
        + activities_total
        + misc_total
    )

    return {
        "accommodation_cost": accommodation_total,
        "transportation_cost": transit_total,
        "food_cost": food_total,
        "activities_cost": activities_total,
        "miscellaneous_cost": misc_total,
        "total_estimated_cost": grand_total,
        "currency": "INR",
        "breakdown_notes": {
            "nights_calculated": nights,
            "total_transit_km": round(total_km, 1),
            "rate_per_km": rate_per_km
        }
    }