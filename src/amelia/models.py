"""Shared data models for Amelia CLI."""

from dataclasses import dataclass


@dataclass
class FlightLeg:
    airline: str
    flight_number: str
    origin: str
    destination: str
    departs: str
    arrives: str
    duration_min: int


@dataclass
class Flight:
    price: int
    duration_min: int
    stops: int
    legs: list[FlightLeg]


@dataclass
class CabinAvailability:
    available: bool
    miles: int | None
    seats: int
    airlines: str
    direct: bool


@dataclass
class Availability:
    id: str
    origin: str
    destination: str
    date: str
    source: str
    cabins: dict[str, CabinAvailability]


@dataclass
class FlightSegment:
    flight_number: str
    aircraft: str
    aircraft_code: str
    fare_class: str
    origin: str
    destination: str
    departs: str
    arrives: str
    distance: int
    order: int


@dataclass
class BookingLink:
    label: str
    url: str
    primary: bool


@dataclass
class TripDetail:
    id: str
    availability_id: str
    segments: list[FlightSegment]
    duration_min: int
    stops: int
    carriers: str
    cabin: str
    miles: int
    taxes: int
    taxes_currency: str
    booking_links: list[BookingLink]


@dataclass
class LiveResult:
    id: str
    segments: list[FlightSegment]
    duration_min: int
    stops: int
    carriers: str
    cabin: str
    miles: int
    taxes: int
    taxes_currency: str
    seats: int
    filtered: bool


@dataclass
class Route:
    id: str
    origin: str
    destination: str
    origin_region: str
    destination_region: str
    distance: int
    source: str


@dataclass
class Hotel:
    name: str
    brand: str | None
    stars: int | None
    rating: float | None
    reviews: int | None
    rate_per_night: int
    total: int
    currency: str
    amenities: list[str]
    url: str
    lat: float | None
    lon: float | None
    distance_miles: float | None


@dataclass
class SearchResult:
    """Wraps API responses to distinguish empty results from errors."""

    data: list
    rate_limit_remaining: int | None
    empty: bool
    error: str | None


@dataclass
class PriceInsight:
    origin: str
    destination: str
    date: str
    cabin: str
    cabin_fallback: str | None
    lowest_price: int | None
    price_level: str | None
    typical_range_low: int | None
    typical_range_high: int | None
    price_history: list[list[int]]  # [[unix_timestamp, price_usd], ...]
    signal: str  # BUY, GOOD, WAIT, HIGH, NO_DATA
