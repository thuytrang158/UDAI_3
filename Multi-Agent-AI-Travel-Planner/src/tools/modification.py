"""ID-constrained itinerary selection changes."""
import json

from langchain_core.messages import SystemMessage, HumanMessage
from src.config import get_llm


def modify_selection_with_llm(feedback, selected_places, available_places, trip_requirements=None):
    """Return only verified candidate objects, preserving all source metadata."""
    # Candidates may still be selected before geocoding succeeds. The itinerary
    # step retries coordinates and clearly marks any remaining unresolved point.
    candidates = list(available_places)
    by_id = {p.get("id"): p for p in candidates if p.get("id")}
    if not by_id:
        by_name = {p.get("name"): p for p in candidates}
    else:
        by_name = {}
    try:
        llm = get_llm(json_mode=True, num_predict=500, temperature=0.1)
        candidate_summaries = [{"id": p.get("id"), "name": p.get("name"), "category": p.get("category"),
                                "description": p.get("description", "")} for p in candidates]
        current = [p.get("id") or p.get("name") for p in selected_places]
        response = llm.invoke([
            SystemMessage(content="Apply the user's place-selection change. Select only IDs supplied by the user input. Return JSON {\"selected_ids\":[...]}; do not invent IDs."),
            HumanMessage(content=json.dumps({"feedback": feedback, "current_ids": current, "candidates": candidate_summaries,
                                            "trip_requirements": trip_requirements or {}}, ensure_ascii=False)),
        ])
        raw = response.content.strip()
        data = json.loads(raw[raw.find("{"):raw.rfind("}") + 1])
        ids = data.get("selected_ids", [])
        lookup = by_id or by_name
        selected = [lookup[key] for key in ids if key in lookup]
        if selected:
            return selected
    except Exception as exc:
        print(f"[Modification warning] Could not apply AI selection: {exc}")
    # If the model is unavailable, retain the current exact objects, allowing users to retry.
    return list(selected_places)
