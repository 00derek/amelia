"""Google Flights search via the flights package (import name: fli)."""

import os

from amelia.models import Flight, FlightLeg, PriceInsight

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


def get_price_insights(
    origin: str,
    destination: str,
    date: str,
    cabin: str = "economy",
) -> PriceInsight:
    """Get Google Flights price insights via SerpAPI."""
    try:
        import serpapi
    except ImportError:
        raise RuntimeError("serpapi package not installed")

    api_key = os.environ.get("SERPAPI_KEY")
    if not api_key:
        raise RuntimeError("SERPAPI_KEY not set")

    return _query_insights(serpapi, origin, destination, date, cabin, api_key)


def _query_insights(
    serpapi_mod,
    origin: str,
    destination: str,
    date: str,
    cabin: str,
    api_key: str,
) -> PriceInsight:
    """Query SerpAPI for price insights, with cabin fallback."""
    travel_class = SERPAPI_CABIN_MAP.get(cabin.lower(), 1)

    result = _fetch_insights(
        serpapi_mod, origin, destination, date, travel_class, api_key
    )
    if result is not None:
        return _build_insight(origin, destination, date, cabin, None, result)

    if cabin.lower() != "economy":
        result = _fetch_insights(serpapi_mod, origin, destination, date, 1, api_key)
        if result is not None:
            return _build_insight(origin, destination, date, cabin, "economy", result)

    return PriceInsight(
        origin=origin,
        destination=destination,
        date=date,
        cabin=cabin,
        cabin_fallback="economy" if cabin.lower() != "economy" else None,
        lowest_price=None,
        price_level=None,
        typical_range_low=None,
        typical_range_high=None,
        price_history=[],
        signal="NO_DATA",
    )


def _fetch_insights(
    serpapi_mod,
    origin: str,
    destination: str,
    date: str,
    travel_class: int,
    api_key: str,
) -> dict | None:
    """Call SerpAPI Google Flights and return price_insights dict, or None."""
    params = {
        "engine": "google_flights",
        "departure_id": origin,
        "arrival_id": destination,
        "outbound_date": date,
        "type": "2",
        "travel_class": travel_class,
        "adults": 1,
        "currency": "USD",
        "hl": "en",
    }
    client = serpapi_mod.Client(api_key=api_key)
    response = client.search(params)
    insights = response.get("price_insights")
    if not insights:
        return None
    if "lowest_price" not in insights and "price_level" not in insights:
        return None
    return insights


def _build_insight(
    origin: str,
    destination: str,
    date: str,
    cabin: str,
    cabin_fallback: str | None,
    raw: dict,
) -> PriceInsight:
    """Build PriceInsight from raw SerpAPI price_insights dict."""
    lowest = raw.get("lowest_price")
    level = raw.get("price_level")
    typical = raw.get("typical_price_range", [])
    range_low = typical[0] if len(typical) >= 2 else None
    range_high = typical[1] if len(typical) >= 2 else None
    history = raw.get("price_history", [])

    signal = derive_signal(lowest, level, range_low, range_high)

    return PriceInsight(
        origin=origin,
        destination=destination,
        date=date,
        cabin=cabin,
        cabin_fallback=cabin_fallback,
        lowest_price=lowest,
        price_level=level,
        typical_range_low=range_low,
        typical_range_high=range_high,
        price_history=history,
        signal=signal,
    )


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
