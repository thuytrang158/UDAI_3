"""Keep neighboring stops together when partitioning a trip into daily routes."""
import math
from typing import List, Dict, Any


def group_places_by_days(places: List[Dict[str, Any]], num_days: int) -> List[List[Dict[str, Any]]]:
    if num_days < 1:
        raise ValueError("A trip must have at least one day")
    buckets = [[] for _ in range(num_days)]
    located = [p for p in places if p.get("latitude") is not None and p.get("longitude") is not None]
    unlocated = [p for p in places if p.get("latitude") is None or p.get("longitude") is None]

    def distance(origin, destination):
        lat = (float(origin["latitude"]) + float(destination["latitude"])) / 2
        return math.hypot((float(origin["latitude"]) - float(destination["latitude"])) * 111,
                          (float(origin["longitude"]) - float(destination["longitude"])) * 111 * math.cos(math.radians(lat)))

    # Start with the first selected stop (normally a required venue), then keep
    # nearby stops adjacent. Contiguous daily groups avoid splitting neighbors
    # across days merely to balance the number of visits.
    ordered = []
    remaining = list(located)
    if remaining:
        ordered.append(remaining.pop(0))
    while remaining:
        nearest = min(range(len(remaining)), key=lambda index: distance(ordered[-1], remaining[index]))
        ordered.append(remaining.pop(nearest))
    if ordered:
        active_days = min(num_days, len(ordered))
        base, extra = divmod(len(ordered), active_days)
        offset = 0
        for day in range(active_days):
            count = base + (1 if day < extra else 0)
            buckets[day] = ordered[offset:offset + count]
            offset += count
    for place in unlocated:
        min(buckets, key=len).append(place)
    return buckets
