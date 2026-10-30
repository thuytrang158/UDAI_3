"""
Consolidated Pydantic Schemas for AI Travel Planner.
Contains all validated data contracts across all agents and tools.
"""
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator


# ======================================================================
# Requirements Schemas
# ======================================================================
Interest = Literal[
    "Trekking & Adventure", "Parks & Leisure", "Heritage & Architecture",
    "Spiritual & Wellness", "Food & Culinary", "Shopping & Bazaars",
]


class ExtractedTripRequirements(BaseModel):
    """Schema for raw data extracted by the LLM during requirements collection."""
    destination: Optional[str] = Field(
        default=None, description="The city or region to visit"
    )
    number_of_days: Optional[int] = Field(
        default=None, description="Duration of the trip in days"
    )
    number_of_travelers: Optional[int] = Field(
        default=None, description="Total number of people travelling"
    )
    budget_per_day: Optional[str] = Field(
        default=None, description="Approximate budget per day per person"
    )
    transportation_preference: Optional[str] = Field(
        default=None, description="Preferred transport mode"
    )
    interests: Optional[List[Interest]] = None
    required_places: Optional[List[str]] = Field(default=None, description="Named places the traveler explicitly wants to include")
    excluded_places: Optional[List[str]] = Field(default=None, description="Named places the traveler explicitly wants to avoid")
    preferences: Optional[List[str]] = Field(default=None, description="Other experience, accessibility, group or accommodation preferences")
    pace: Optional[Literal["relaxed", "balanced", "active"]] = None

    @field_validator("destination", "budget_per_day", "transportation_preference", mode="before")
    @classmethod
    def normalize_missing_text(cls, value):
        if isinstance(value, str):
            value = value.strip()
            if value.casefold() in {"", "null", "none", "unknown", "không rõ", "chưa rõ"}:
                return None
        return value

    @field_validator("number_of_days")
    @classmethod
    def validate_days(cls, value):
        if value is not None and value <= 0:
            raise ValueError("Number of days must be at least 1")
        if value is not None and value > 30:
            raise ValueError("Trips longer than 30 days are not supported in V1")
        return value

    @field_validator("number_of_travelers")
    @classmethod
    def validate_travelers(cls, value):
        if value is not None and value <= 0:
            raise ValueError("Number of travelers must be at least 1")
        return value

    @field_validator("destination")
    @classmethod
    def validate_destination(cls, value):
        if value is not None:
            cleaned = value.strip().title()
            if len(cleaned) < 2:
                raise ValueError("Destination name is too short")
            return cleaned
        return value


# ======================================================================
# Place & Attraction Schemas
# ======================================================================
class Place(BaseModel):
    """A source-grounded place; coordinates can be unavailable without hiding its profile."""
    id: str = ""
    name: str = Field(description="Official name of the place")
    category: str = Field(description="Category (Trekking, Feel Good, Heritage, etc.)")
    description: str = Field(description="Brief description of the place")
    latitude: Optional[float] = Field(default=None, description="Verified GPS latitude")
    longitude: Optional[float] = Field(default=None, description="Verified GPS longitude")
    introduction: str = ""
    address: Optional[str] = None
    images: List[str] = Field(default_factory=list)
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    geocoding_status: str = "unavailable"
    geocoding_reason: Optional[str] = None
    coordinate_source: Optional[str] = None
    coordinate_attribution: Optional[str] = None
    reference_data: Dict[str, Any] = Field(default_factory=dict)
    required_for: List[str] = Field(default_factory=list)
    recommendation_reason: str = ""


class DestinationPlaces(BaseModel):
    """Collection of places returned for the destination."""
    destination: str
    places: List[Place]


# ======================================================================
# Routing Schemas (OSRM)
# ======================================================================
class RouteSegment(BaseModel):
    """Represents a verified driving leg between two locations."""
    origin_name: str
    destination_name: str
    distance_km: float = Field(description="Distance in kilometers")
    duration_minutes: int = Field(description="Travel time in minutes")
    source: str = Field(description="'OSRM Live Engine' or 'Haversine Fallback'")


# ======================================================================
# Itinerary Schemas
# ======================================================================
class ActivitySchedule(BaseModel):
    time: str = Field(description="Time of day, e.g. '09:00 AM'")
    activity: str = Field(description="Name of place or event")
    details: str = Field(description="Transit info, notes, or tips")


class DaySchedule(BaseModel):
    day_number: int
    theme: str
    schedule: List[ActivitySchedule]


class TripItinerary(BaseModel):
    destination: str
    total_days: int
    days: List[DaySchedule]


# ======================================================================
# Accommodation Schemas
# ======================================================================
class AccommodationOption(BaseModel):
    """Represents an authentic property with booking link."""
    name: str = Field(description="Property name")
    stay_type: str = Field(description="Hotel, Hostel, Apartment, or Villa")
    area_type: str = Field(description="City Center, Near Transit, Quiet Area, etc.")
    price_per_night: int = Field(description="Estimated nightly rate in VND")
    rating: float = Field(description="User review rating out of 5.0")
    latitude: float
    longitude: float
    booking_url: str = Field(description="Direct or aggregator search link")
    disclaimer: str = Field(
        default="Recommended stay. Availability/price should be verified on the booking provider."
    )


# ======================================================================
# Cost Breakdown Schema
# ======================================================================
class TripCostBreakdown(BaseModel):
    """Deterministic financial breakdown calculated in Python."""
    accommodation_cost: int = Field(description="Total lodging expense for all nights")
    transportation_cost: int = Field(description="Total transit and cab expenses based on mileage")
    food_cost: int = Field(description="Estimated dining and meal expense")
    activities_cost: int = Field(description="Estimated entrance fees and permits")
    miscellaneous_cost: int = Field(description="Buffer for shopping, tips, emergencies")
    total_estimated_cost: int = Field(description="Total sum of all categories")
    currency: str = Field(default="VND")
