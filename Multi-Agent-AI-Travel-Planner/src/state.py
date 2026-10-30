"""
State definition for Phase 9: Final Planner & Cost Integration.
"""
from typing import TypedDict, List, Dict, Any, Optional, Annotated
import operator


class TripPlannerState(TypedDict, total=False):
    messages: Annotated[List[str], operator.add]

    destination: str
    number_of_days: int
    number_of_travelers: int
    budget_per_day: str
    transportation_preference: str
    interests: List[str]
    trip_requirements: Dict[str, Any]

    available_places: List[Dict[str, Any]]
    selected_places: List[Dict[str, Any]]
    routes: List[Dict[str, Any]]
    itinerary: Dict[str, Any]

    itinerary_approved: bool
    approval_status: str
    user_feedback: Optional[str]

    accommodation_preferences: Dict[str, Any]
    accommodation_options: List[Dict[str, Any]]
    selected_accommodation: Dict[str, Any]

    # --- NEW: Phase 9 Final Fields ---
    estimated_cost: Dict[str, Any]
    final_trip_summary: Dict[str, Any]
