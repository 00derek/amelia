"""Amelia CLI — travel agent for flights, awards, and hotels."""

import json
import os
import sys

import click

from amelia.awards import SeatsAeroClient, PROGRAMS
from amelia.config import bootstrap_amelia_dir, load_config, resolve_config
from amelia.output import to_json, to_json_str


def _error(message: str, code: str, exit_code: int = 1):
    """Write JSON error to stderr and exit."""
    json.dump({"error": message, "code": code}, sys.stderr)
    sys.exit(exit_code)


def _get_api_key() -> str:
    key = os.environ.get("SEATS_AERO_API_KEY", "")
    if not key:
        _error(
            "SEATS_AERO_API_KEY not set. See .env.example.", "AUTH_MISSING", exit_code=2
        )
    return key


@click.group()
def main():
    """Amelia — travel agent CLI for flights, awards, and hotels."""
    bootstrap_amelia_dir()


# --- Awards ---


@main.group()
def awards():
    """Award flight search via Seats.aero API."""
    pass


@awards.command()
def programs():
    """List available mileage programs."""
    print(to_json_str(PROGRAMS))


@awards.command()
@click.option("--source", required=True, help="Mileage program name")
def routes(source):
    """List routes for a mileage program."""
    client = SeatsAeroClient(api_key=_get_api_key())
    result = client.routes(source=source)
    if result.error:
        _error(result.error, "API_ERROR")
    print(to_json_str(to_json(result.data)))


@awards.command()
@click.option(
    "--from", "origin", required=True, help="Origin airport(s), comma-separated"
)
@click.option(
    "--to", "destination", required=True, help="Destination airport(s), comma-separated"
)
@click.option("--date", "start_date", required=True, help="Start date YYYY-MM-DD")
@click.option("--end-date", default=None, help="End date YYYY-MM-DD")
@click.option("--cabin", default=None, help="Cabin: economy,premium,business,first")
@click.option("--carriers", default=None, help="Airline filter, comma-separated")
@click.option("--sources", default=None, help="Program filter, comma-separated")
@click.option("--direct", is_flag=True, help="Nonstop only")
@click.option("--limit", default=50, type=int, help="Max results")
@click.option(
    "--sort", default=None, help="Sort: miles (API), or seats,date,taxes (client-side)"
)
def search(
    origin,
    destination,
    start_date,
    end_date,
    cabin,
    carriers,
    sources,
    direct,
    limit,
    sort,
):
    """Search cached award availability."""
    client = SeatsAeroClient(api_key=_get_api_key())
    order_by = "lowest_mileage" if sort == "miles" else None
    result = client.search(
        origin=origin,
        destination=destination,
        start_date=start_date,
        end_date=end_date,
        cabins=cabin,
        sources=sources,
        carriers=carriers,
        direct=direct,
        order_by=order_by,
        limit=limit,
    )
    if result.error:
        _error(result.error, "API_ERROR")

    data = result.data
    # Client-side sorting for non-API sort keys
    if sort and sort != "miles" and data:
        if sort == "seats":
            data.sort(
                key=lambda a: max(c.seats for c in a.cabins.values()), reverse=True
            )
        elif sort == "date":
            data.sort(key=lambda a: a.date)
        elif sort == "taxes":
            pass  # Taxes not available at availability level, only at trip level

    # Rate limit info to stderr for skills to read
    if result.rate_limit_remaining is not None:
        json.dump({"rate_limit_remaining": result.rate_limit_remaining}, sys.stderr)
    print(to_json_str(data))


@awards.command("trip")
@click.argument("availability_id")
def trip_cmd(availability_id):
    """Get trip details and booking links."""
    client = SeatsAeroClient(api_key=_get_api_key())
    result = client.trip(availability_id=availability_id)
    if result.error:
        _error(result.error, "API_ERROR")
    print(to_json_str(to_json(result.data)))


@awards.command()
@click.option("--source", required=True, help="Mileage program")
@click.option("--cabin", default=None, help="Cabin class")
@click.option("--start-date", default=None, help="Start date YYYY-MM-DD")
@click.option("--end-date", default=None, help="End date YYYY-MM-DD")
@click.option("--origin-region", default=None, help="Origin region")
@click.option("--dest-region", default=None, help="Destination region")
@click.option("--limit", default=50, type=int, help="Max results")
def availability(
    source, cabin, start_date, end_date, origin_region, dest_region, limit
):
    """Bulk availability for a mileage program."""
    client = SeatsAeroClient(api_key=_get_api_key())
    result = client.availability(
        source=source,
        cabin=cabin,
        start_date=start_date,
        end_date=end_date,
        origin_region=origin_region,
        dest_region=dest_region,
        limit=limit,
    )
    if result.error:
        _error(result.error, "API_ERROR")
    print(to_json_str(to_json(result.data)))


@awards.command()
@click.option("--from", "origin", required=True, help="Origin airport")
@click.option("--to", "destination", required=True, help="Destination airport")
@click.option("--date", required=True, help="Departure date YYYY-MM-DD")
@click.option("--source", required=True, help="Mileage program")
@click.option("--seats", default=1, type=int, help="Passenger count 1-9")
@click.option("--disable-filters", is_flag=True, help="Disable dynamic pricing filters")
def live(origin, destination, date, source, seats, disable_filters):
    """Real-time award search."""
    client = SeatsAeroClient(api_key=_get_api_key())
    result = client.live(
        origin=origin,
        destination=destination,
        date=date,
        source=source,
        seat_count=seats,
        disable_filters=disable_filters,
    )
    if result.error:
        _error(result.error, "API_ERROR")
    print(to_json_str(to_json(result.data)))


# --- Flights ---


@main.group()
def flights():
    """Cash flight search via Google Flights."""
    pass


@flights.command("search")
@click.option("--from", "origin", required=True, help="Origin IATA code")
@click.option("--to", "destination", required=True, help="Destination IATA code")
@click.option("--date", required=True, help="Departure date YYYY-MM-DD")
@click.option(
    "--cabin", default="economy", help="economy, premium_economy, business, first"
)
@click.option("--stops", default="ANY", help="ANY, 0, 1, 2")
@click.option(
    "--sort", default="cheapest", help="cheapest, duration, departure, arrival"
)
@click.option(
    "--time", "time_window", default=None, help="Departure window, e.g. 15-23"
)
@click.option(
    "--airlines", default=None, help="Airline codes, comma-separated (e.g. UA,DL)"
)
def flights_search(
    origin, destination, date, cabin, stops, sort, time_window, airlines
):
    """Search one-way cash flights."""
    from amelia.flights import search as flight_search

    airline_list = [a.strip() for a in airlines.split(",")] if airlines else None
    try:
        results = flight_search(
            origin=origin,
            destination=destination,
            date=date,
            cabin=cabin,
            stops=stops,
            sort=sort,
            time_window=time_window,
            airlines=airline_list,
        )
    except RuntimeError as e:
        _error(str(e), "SEARCH_ERROR")

    print(to_json_str(to_json(results)))


@flights.command("insights")
@click.option("--from", "origin", required=True, help="Origin IATA code")
@click.option("--to", "destination", required=True, help="Destination IATA code")
@click.option("--date", required=True, help="Departure date YYYY-MM-DD")
@click.option(
    "--cabin", default="economy", help="economy, premium_economy, business, first"
)
def flights_insights(origin, destination, date, cabin):
    """Get price insights — is now a good time to buy?"""
    from amelia.flights import get_price_insights
    import requests

    try:
        result = get_price_insights(
            origin=origin,
            destination=destination,
            date=date,
            cabin=cabin,
        )
    except RuntimeError as e:
        if "SERPAPI_KEY" in str(e):
            _error(str(e), "AUTH_MISSING", exit_code=2)
        else:
            _error(str(e), "SEARCH_ERROR")
    except (requests.RequestException, ConnectionError, TimeoutError) as e:
        _error(f"Network error: {e}", "NETWORK_ERROR", exit_code=4)

    print(to_json_str(to_json(result)))


# --- Hotels ---


@main.group()
def hotels():
    """Hotel search via Google Hotels."""
    pass


@hotels.command("search")
@click.option("--city", required=True, help="City name or IATA code")
@click.option("--checkin", required=True, help="Check-in YYYY-MM-DD")
@click.option("--checkout", required=True, help="Check-out YYYY-MM-DD")
@click.option("--adults", default=2, type=int, help="Number of adults")
@click.option("--min-price", default=None, type=int, help="Min rate/night")
@click.option("--max-price", default=None, type=int, help="Max rate/night")
@click.option("--stars", default=None, help="Comma-separated star ratings")
@click.option("--brands", default=None, help="Comma-separated brand names")
@click.option("--sort", default="price", help="price, rating, reviews")
@click.option("--limit", default=None, type=int, help="Max results")
@click.option("--currency", default="USD", help="Currency code")
@click.option("--lat", default=None, type=float, help="Venue latitude")
@click.option("--lon", default=None, type=float, help="Venue longitude")
@click.option("--max-distance", default=None, type=float, help="Max distance in miles")
def hotels_search(
    city,
    checkin,
    checkout,
    adults,
    min_price,
    max_price,
    stars,
    brands,
    sort,
    limit,
    currency,
    lat,
    lon,
    max_distance,
):
    """Search hotels for a city and date range."""
    from amelia.hotels import search as hotel_search, post_filter

    try:
        results = hotel_search(
            city=city,
            checkin=checkin,
            checkout=checkout,
            adults=adults,
            sort=sort,
            currency=currency,
            min_price=min_price,
            max_price=max_price,
            stars=stars,
            brands=brands,
        )
    except RuntimeError as e:
        _error(str(e), "SEARCH_ERROR")

    # Post-filter (distance, plus re-apply price/stars/brands to catch API misses)
    results = post_filter(
        results,
        min_price=min_price,
        max_price=max_price,
        stars=stars,
        brands=brands,
        limit=limit,
        lat=lat,
        lon=lon,
        max_distance=max_distance,
    )

    print(to_json_str(to_json(results)))


# --- Config ---


@main.group()
def config():
    """View and manage configuration."""
    pass


@config.command()
@click.option("--profile", default=None, help="Profile to resolve")
def show(profile):
    """Show resolved configuration."""
    cfg = load_config()
    resolved = resolve_config(cfg, profile=profile)
    print(json.dumps(resolved, indent=2))
