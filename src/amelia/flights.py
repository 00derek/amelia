"""Google Flights search via the flights package (import name: fli)."""

from amelia.models import Flight, FlightLeg

CABIN_MAP = {
    "economy": "ECONOMY",
    "premium_economy": "PREMIUM_ECONOMY",
    "business": "BUSINESS",
    "first": "FIRST",
}

SORT_MAP = {
    "cheapest": "CHEAPEST",
    "duration": "DURATION",
    "departure": "DEPARTURE_TIME",
    "arrival": "ARRIVAL_TIME",
}

SERPAPI_CABIN_MAP = {
    "economy": 1,
    "premium_economy": 2,
    "business": 3,
    "first": 4,
}


def derive_signal(
    lowest_price: int | None,
    price_level: str | None,
    typical_range_low: int | None,
    typical_range_high: int | None,
) -> str:
    """Derive buy/wait signal from price insights data.

    Returns: BUY, GOOD, WAIT, HIGH, or NO_DATA.
    """
    has_range = typical_range_low is not None and typical_range_high is not None
    has_level = price_level is not None

    if has_range and lowest_price is not None:
        if lowest_price <= typical_range_low:
            return "BUY"
        if price_level == "low":
            return "GOOD"
        if price_level == "high":
            return "HIGH"
        return "WAIT"

    if has_level:
        if price_level == "low":
            return "GOOD"
        if price_level == "high":
            return "HIGH"
        return "WAIT"

    return "NO_DATA"


def flight_to_model(flight) -> Flight:
    """Convert a fli FlightResult to our Flight dataclass."""
    return Flight(
        price=flight.price,
        duration_min=flight.duration,
        stops=flight.stops,
        legs=[
            FlightLeg(
                airline=leg.airline.name,
                flight_number=leg.flight_number,
                origin=leg.departure_airport.name,
                destination=leg.arrival_airport.name,
                departs=leg.departure_datetime.isoformat(),
                arrives=leg.arrival_datetime.isoformat(),
                duration_min=leg.duration,
            )
            for leg in flight.legs
        ],
    )


def search(
    origin: str,
    destination: str,
    date: str,
    cabin: str = "economy",
    stops: str = "ANY",
    sort: str = "cheapest",
    time_window: str | None = None,
    airlines: list[str] | None = None,
) -> list[Flight]:
    """Search Google Flights for one-way cash flights.

    Returns list of Flight dataclasses. Raises RuntimeError on import or search failure.
    """
    try:
        from fli.core import (
            build_flight_segments,
            build_time_restrictions,
            parse_airlines,
            parse_cabin_class,
            parse_max_stops,
            parse_sort_by,
            resolve_airport,
        )
        from fli.models import FlightSearchFilters, PassengerInfo
        from fli.search import SearchFlights
    except ImportError as e:
        raise RuntimeError(f"flights package not installed: {e}")

    resolve_airport(origin)
    resolve_airport(destination)

    time_restrictions = None
    if time_window:
        time_restrictions = build_time_restrictions(departure_window=time_window)

    cabin_value = CABIN_MAP.get(cabin.lower(), cabin.upper())
    sort_value = SORT_MAP.get(sort.lower(), sort.upper())

    segments, trip_type = build_flight_segments(
        origin=resolve_airport(origin),
        destination=resolve_airport(destination),
        departure_date=date,
        return_date=None,
        time_restrictions=time_restrictions,
    )

    filters = FlightSearchFilters(
        trip_type=trip_type,
        passenger_info=PassengerInfo(adults=1),
        flight_segments=segments,
        stops=parse_max_stops(stops.upper()),
        seat_type=parse_cabin_class(cabin_value),
        airlines=parse_airlines(airlines) if airlines else None,
        sort_by=parse_sort_by(sort_value),
    )

    searcher = SearchFlights()
    results = searcher.search(filters)

    if not results:
        return []

    return [flight_to_model(f) for f in results]
