"""
OSRM (Open Source Routing Machine) Routing Tool.
Calculates road distance and travel time between coordinates deterministically.
"""
import json
import math
import urllib.request
from typing import Dict, Any


def haversine_fallback(
    origin_lat: float, origin_lon: float,
    dest_lat: float, dest_lon: float
) -> Dict[str, Any]:
    """
    Calculates great-circle distance as an offline fallback when OSRM is unreachable.
    Applies realistic city traffic speeds (~25 km/h for short distances, ~45 km/h for outer roads).
    """
    radius_earth_km = 6371.0

    d_lat = math.radians(dest_lat - origin_lat)
    d_lon = math.radians(dest_lon - origin_lon)
    lat1 = math.radians(origin_lat)
    lat2 = math.radians(dest_lat)

    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(d_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Road routing is typically ~1.25x to 1.35x longer than straight-line distance
    road_distance_km = round(radius_earth_km * c * 1.3, 1)

    # Estimate duration based on distance
    if road_distance_km > 30:
        avg_speed_kmh = 45.0  # Highway / outer ring
    else:
        avg_speed_kmh = 22.0  # Inner-city traffic speed

    duration_minutes = max(int((road_distance_km / avg_speed_kmh) * 60), 5)

    return {
        "distance_km": road_distance_km,
        "duration_minutes": duration_minutes,
        "source": "Haversine Fallback (Calculated)",
    }


def calculate_route(
    origin_lat: float, origin_lon: float,
    dest_lat: float, dest_lon: float
) -> Dict[str, Any]:
    """
    Queries the open-source OSRM routing service.
    NOTE: OSRM expects coordinates in {lon},{lat} order!
    """
    # Build standard OSRM driving URL
    # Format: http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false
    url = (
        f"http://router.project-osrm.org/route/v1/driving/"
        f"{origin_lon},{origin_lat};{dest_lon},{dest_lat}?overview=false"
    )

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "OpenSource-AI-Travel-Planner-V1"}
        )
        with urllib.request.urlopen(req, timeout=4) as response:
            data = json.loads(response.read().decode("utf-8"))

        if data.get("code") == "Ok" and data.get("routes"):
            route = data["routes"][0]
            # OSRM returns distance in meters and duration in seconds
            distance_km = round(route["distance"] / 1000.0, 1)
            duration_minutes = max(int(round(route["duration"] / 60.0)), 1)

            return {
                "distance_km": distance_km,
                "duration_minutes": duration_minutes,
                "source": "OSRM Live Engine",
            }

    except Exception as exc:
        print(f"[Tool: routing.py] Live OSRM unavailable ({exc}). Using deterministic fallback.")

    # Offline / rate-limit fallback
    return haversine_fallback(origin_lat, origin_lon, dest_lat, dest_lon)
