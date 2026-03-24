"""Seats.aero API client — clean-room implementation from API docs."""

import requests

from amelia.models import (
    Availability,
    CabinAvailability,
    FlightSegment,
    TripDetail,
    BookingLink,
    LiveResult,
    Route,
    SearchResult,
)

BASE_URL = "https://seats.aero/partnerapi"

PROGRAMS = sorted(
    [
        "aeroplan",
        "aeromexico",
        "alaska",
        "american",
        "azul",
        "connectmiles",
        "delta",
        "emirates",
        "ethiopian",
        "etihad",
        "eurobonus",
        "finnair",
        "flyingblue",
        "jetblue",
        "lufthansa",
        "qantas",
        "qatar",
        "saudia",
        "singapore",
        "smiles",
        "turkish",
        "united",
        "velocity",
        "virginatlantic",
    ]
)

REGIONS = [
    "North America",
    "South America",
    "Africa",
    "Asia",
    "Europe",
    "Oceania",
]


class SeatsAeroClient:
    """Client for the Seats.aero Partner API."""

    def __init__(self, api_key: str):
        self.api_key = api_key

    def _headers(self) -> dict:
        return {"Partner-Authorization": self.api_key}

    def _extract_rate_limit(self, response) -> int | None:
        val = response.headers.get("x-ratelimit-remaining")
        return int(val) if val else None

    def _get(self, path: str, params: dict | None = None) -> tuple:
        """Make GET request. Returns (response, error_string_or_None)."""
        try:
            resp = requests.get(
                f"{BASE_URL}/{path}",
                headers=self._headers(),
                params=params or {},
                timeout=30,
            )
        except requests.RequestException as e:
            return None, f"Network error: {e}"

        if resp.status_code == 401 or resp.status_code == 403:
            return (
                resp,
                f"Auth error (HTTP {resp.status_code}): check SEATS_AERO_API_KEY",
            )
        if resp.status_code == 429:
            return resp, "Rate limited: 1,000 calls/day exceeded"
        if resp.status_code >= 400:
            return resp, f"API error (HTTP {resp.status_code})"

        return resp, None

    def _post(self, path: str, body: dict) -> tuple:
        """Make POST request. Returns (response, error_string_or_None)."""
        try:
            resp = requests.post(
                f"{BASE_URL}/{path}",
                headers={**self._headers(), "Content-Type": "application/json"},
                json=body,
                timeout=60,
            )
        except requests.RequestException as e:
            return None, f"Network error: {e}"

        if resp.status_code == 401 or resp.status_code == 403:
            return (
                resp,
                f"Auth error (HTTP {resp.status_code}): check SEATS_AERO_API_KEY",
            )
        if resp.status_code == 429:
            return resp, "Rate limited: 1,000 calls/day exceeded"
        if resp.status_code >= 400:
            return resp, f"API error (HTTP {resp.status_code})"

        return resp, None

    def _parse_availability(self, raw: dict) -> Availability:
        """Parse a raw availability object from the API."""
        route = raw.get("Route", {})
        cabins = {}
        for letter in ("Y", "W", "J", "F"):
            cost_str = raw.get(f"{letter}MileageCost", "0")
            cabins[letter] = CabinAvailability(
                available=raw.get(f"{letter}Available", False),
                miles=int(cost_str) if cost_str and cost_str != "0" else None,
                seats=raw.get(f"{letter}RemainingSeats", 0),
                airlines=raw.get(f"{letter}Airlines", ""),
                direct=raw.get(f"{letter}Direct", False),
            )
        return Availability(
            id=raw["ID"],
            origin=route.get("OriginAirport", ""),
            destination=route.get("DestinationAirport", ""),
            date=raw.get("Date", ""),
            source=raw.get("Source", ""),
            cabins=cabins,
        )

    def programs(self) -> list[str]:
        """Return hardcoded list of known mileage programs."""
        return list(PROGRAMS)

    def routes(self, source: str) -> SearchResult:
        """Get routes for a mileage program."""
        resp, err = self._get("routes", params={"source": source})
        if err:
            rl = self._extract_rate_limit(resp) if resp else None
            return SearchResult(
                data=[], rate_limit_remaining=rl, empty=False, error=err
            )

        rate_limit = self._extract_rate_limit(resp)
        raw = resp.json()

        if not raw:
            return SearchResult(
                data=[], rate_limit_remaining=rate_limit, empty=True, error=None
            )

        routes = [
            Route(
                id=r["ID"],
                origin=r["OriginAirport"],
                destination=r["DestinationAirport"],
                origin_region=r.get("OriginRegion", ""),
                destination_region=r.get("DestinationRegion", ""),
                distance=r.get("Distance", 0),
                source=r.get("Source", source),
            )
            for r in raw
        ]
        return SearchResult(
            data=routes, rate_limit_remaining=rate_limit, empty=False, error=None
        )

    def search(
        self,
        origin: str,
        destination: str,
        start_date: str | None = None,
        end_date: str | None = None,
        cabins: str | None = None,
        sources: str | None = None,
        carriers: str | None = None,
        direct: bool = False,
        order_by: str | None = None,
        limit: int = 500,
    ) -> SearchResult:
        """Cached search for award availability."""
        params = {
            "origin_airport": origin,
            "destination_airport": destination,
        }
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if cabins:
            params["cabins"] = cabins
        if sources:
            params["sources"] = sources
        if carriers:
            params["carriers"] = carriers
        if direct:
            params["only_direct_flights"] = "true"
        if order_by:
            params["order_by"] = order_by

        # Paginate
        all_results = []
        seen_ids = set()
        params["take"] = min(limit, 500)
        rate_limit = None

        while len(all_results) < limit:
            resp, err = self._get("search", params=params)
            if err:
                rl = self._extract_rate_limit(resp) if resp else None
                if all_results:
                    return SearchResult(
                        data=all_results,
                        rate_limit_remaining=rl,
                        empty=False,
                        error=None,
                    )
                return SearchResult(
                    data=[], rate_limit_remaining=rl, empty=False, error=err
                )

            rate_limit = self._extract_rate_limit(resp)
            body = resp.json()
            data = body.get("data", [])

            for item in data:
                if item["ID"] not in seen_ids:
                    seen_ids.add(item["ID"])
                    all_results.append(self._parse_availability(item))

            if not body.get("hasMore", False):
                break

            params["cursor"] = body.get("cursor")
            params["skip"] = len(seen_ids)

        if not all_results:
            return SearchResult(
                data=[], rate_limit_remaining=rate_limit, empty=True, error=None
            )

        return SearchResult(
            data=all_results[:limit],
            rate_limit_remaining=rate_limit,
            empty=False,
            error=None,
        )

    def trip(
        self, availability_id: str, include_filtered: bool = False
    ) -> SearchResult:
        """Get trip details and booking links for an availability."""
        params = {}
        if include_filtered:
            params["include_filtered"] = "true"

        resp, err = self._get(f"trips/{availability_id}", params=params)
        if err:
            rl = self._extract_rate_limit(resp) if resp else None
            return SearchResult(
                data=[], rate_limit_remaining=rl, empty=False, error=err
            )

        rate_limit = self._extract_rate_limit(resp)
        body = resp.json()
        trips_data = body.get("data", [])
        booking_links_raw = body.get("booking_links", [])

        booking_links = [
            BookingLink(
                label=bl.get("label", ""),
                url=bl.get("link", ""),
                primary=bl.get("primary", False),
            )
            for bl in booking_links_raw
        ]

        if not trips_data:
            return SearchResult(
                data=[], rate_limit_remaining=rate_limit, empty=True, error=None
            )

        # Return the first trip (most relevant)
        raw = trips_data[0]
        segments = [
            FlightSegment(
                flight_number=seg.get("FlightNumber", ""),
                aircraft=seg.get("AircraftName", ""),
                aircraft_code=seg.get("AircraftCode", ""),
                fare_class=seg.get("FareClass", ""),
                origin=seg.get("OriginAirport", ""),
                destination=seg.get("DestinationAirport", ""),
                departs=seg.get("DepartsAt", ""),
                arrives=seg.get("ArrivesAt", ""),
                distance=seg.get("Distance", 0),
                order=seg.get("Order", 0),
            )
            for seg in sorted(
                raw.get("AvailabilitySegments", []), key=lambda s: s.get("Order", 0)
            )
        ]

        trip_detail = TripDetail(
            id=raw["ID"],
            availability_id=raw.get("AvailabilityID", availability_id),
            segments=segments,
            duration_min=raw.get("TotalDuration", 0),
            stops=raw.get("Stops", 0),
            carriers=raw.get("Carriers", ""),
            cabin=raw.get("Cabin", ""),
            miles=raw.get("MileageCost", 0),
            taxes=raw.get("TotalTaxes", 0),
            taxes_currency=raw.get("TaxesCurrency", "USD"),
            booking_links=booking_links,
        )

        return SearchResult(
            data=trip_detail,
            rate_limit_remaining=rate_limit,
            empty=False,
            error=None,
        )

    def availability(
        self,
        source: str,
        cabin: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        origin_region: str | None = None,
        dest_region: str | None = None,
        limit: int = 500,
    ) -> SearchResult:
        """Bulk availability for a mileage program."""
        params = {"source": source}
        if cabin:
            params["cabin"] = cabin
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if origin_region:
            params["origin_region"] = origin_region
        if dest_region:
            params["destination_region"] = dest_region

        # Paginate (same pattern as search)
        all_results = []
        seen_ids = set()
        params["take"] = min(limit, 500)
        rate_limit = None

        while len(all_results) < limit:
            resp, err = self._get("availability", params=params)
            if err:
                rl = self._extract_rate_limit(resp) if resp else None
                if all_results:
                    return SearchResult(
                        data=all_results,
                        rate_limit_remaining=rl,
                        empty=False,
                        error=None,
                    )
                return SearchResult(
                    data=[], rate_limit_remaining=rl, empty=False, error=err
                )

            rate_limit = self._extract_rate_limit(resp)
            body = resp.json()

            for item in body.get("data", []):
                if item["ID"] not in seen_ids:
                    seen_ids.add(item["ID"])
                    all_results.append(self._parse_availability(item))

            if not body.get("hasMore", False):
                break
            params["cursor"] = body.get("cursor")
            params["skip"] = len(seen_ids)

        if not all_results:
            return SearchResult(
                data=[], rate_limit_remaining=rate_limit, empty=True, error=None
            )
        return SearchResult(
            data=all_results[:limit],
            rate_limit_remaining=rate_limit,
            empty=False,
            error=None,
        )

    def live(
        self,
        origin: str,
        destination: str,
        date: str,
        source: str,
        seat_count: int = 1,
        disable_filters: bool = False,
    ) -> SearchResult:
        """Real-time award search."""
        body = {
            "origin_airport": origin,
            "destination_airport": destination,
            "departure_date": date,
            "source": source,
        }
        if seat_count > 1:
            body["seat_count"] = seat_count
        if disable_filters:
            body["disable_filters"] = True

        resp, err = self._post("live", body=body)
        if err:
            rl = self._extract_rate_limit(resp) if resp else None
            return SearchResult(
                data=[], rate_limit_remaining=rl, empty=False, error=err
            )

        rate_limit = self._extract_rate_limit(resp)
        raw_results = resp.json().get("results", [])

        if not raw_results:
            return SearchResult(
                data=[], rate_limit_remaining=rate_limit, empty=True, error=None
            )

        results = []
        for raw in raw_results:
            segments = [
                FlightSegment(
                    flight_number=seg.get("FlightNumber", ""),
                    aircraft=seg.get("AircraftName", ""),
                    aircraft_code=seg.get("AircraftCode", ""),
                    fare_class=seg.get("FareClass", ""),
                    origin=seg.get("OriginAirport", ""),
                    destination=seg.get("DestinationAirport", ""),
                    departs=seg.get("DepartsAt", ""),
                    arrives=seg.get("ArrivesAt", ""),
                    distance=seg.get("Distance", 0),
                    order=seg.get("Order", 0),
                )
                for seg in sorted(
                    raw.get("AvailabilitySegments", []), key=lambda s: s.get("Order", 0)
                )
            ]
            results.append(
                LiveResult(
                    id=raw.get("ID", ""),
                    segments=segments,
                    duration_min=raw.get("TotalDuration", 0),
                    stops=raw.get("Stops", 0),
                    carriers=raw.get("Carriers", ""),
                    cabin=raw.get("Cabin", ""),
                    miles=raw.get("MileageCost", 0),
                    taxes=raw.get("TotalTaxes", 0),
                    taxes_currency=raw.get("TaxesCurrency", "USD"),
                    seats=raw.get("RemainingSeats", 0),
                    filtered=raw.get("Filtered", False),
                )
            )

        return SearchResult(
            data=results, rate_limit_remaining=rate_limit, empty=False, error=None
        )
