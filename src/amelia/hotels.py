"""Hotel search via SerpAPI (primary) and fast-hotels (fallback)."""

import json
import math
import os
import sys

from amelia.models import Hotel

IATA_TO_CITY = {
    "SFO": "San Francisco",
    "LAX": "Los Angeles",
    "JFK": "New York",
    "ORD": "Chicago",
    "BOS": "Boston",
    "DFW": "Dallas",
    "SEA": "Seattle",
    "MIA": "Miami",
    "ATL": "Atlanta",
    "DEN": "Denver",
    "IAD": "Washington",
    "TPE": "Taipei",
    "NRT": "Tokyo",
    "HND": "Tokyo",
    "ICN": "Seoul",
    "HKG": "Hong Kong",
    "SIN": "Singapore",
    "BKK": "Bangkok",
    "LHR": "London",
    "CDG": "Paris",
    "FCO": "Rome",
    "GRU": "Sao Paulo",
    "GIG": "Rio de Janeiro",
    "JPA": "Joao Pessoa",
    "CUN": "Cancun",
    "MEX": "Mexico City",
    "YVR": "Vancouver",
    "YYZ": "Toronto",
    "SYD": "Sydney",
    "AKL": "Auckland",
}

SORT_MAP = {"price": 3, "rating": 8, "reviews": 13}

BRAND_IDS = {
    "marriott": 46,
    "hyatt": 37,
    "hilton": 28,
    "ihg": 17,
}

BRAND_MAP = [
    ("Courtyard", "Marriott"),
    ("Residence Inn", "Marriott"),
    ("Fairfield", "Marriott"),
    ("SpringHill", "Marriott"),
    ("TownePlace", "Marriott"),
    ("Moxy", "Marriott"),
    ("AC Hotel", "Marriott"),
    ("Aloft", "Marriott"),
    ("Element", "Marriott"),
    ("Westin", "Marriott"),
    ("Sheraton", "Marriott"),
    ("W Hotel", "Marriott"),
    ("St. Regis", "Marriott"),
    ("Ritz-Carlton", "Marriott"),
    ("Marriott", "Marriott"),
    ("Hyatt Place", "Hyatt"),
    ("Hyatt House", "Hyatt"),
    ("Hyatt Regency", "Hyatt"),
    ("Hyatt Centric", "Hyatt"),
    ("Grand Hyatt", "Hyatt"),
    ("Hyatt", "Hyatt"),
    ("Hampton", "Hilton"),
    ("Embassy Suites", "Hilton"),
    ("Doubletree", "Hilton"),
    ("DoubleTree", "Hilton"),
    ("Tru by Hilton", "Hilton"),
    ("Home2 Suites", "Hilton"),
    ("Homewood Suites", "Hilton"),
    ("Conrad", "Hilton"),
    ("Curio", "Hilton"),
    ("Tapestry", "Hilton"),
    ("Hilton", "Hilton"),
    ("Holiday Inn", "IHG"),
    ("Crowne Plaza", "IHG"),
    ("Staybridge", "IHG"),
    ("Candlewood", "IHG"),
    ("InterContinental", "IHG"),
    ("Kimpton", "IHG"),
    ("IHG", "IHG"),
    ("Best Western", "Best Western"),
    ("Wyndham", "Wyndham"),
    ("La Quinta", "Wyndham"),
    ("Ramada", "Wyndham"),
    ("Days Inn", "Wyndham"),
    ("Super 8", "Wyndham"),
    ("Motel 6", "Motel 6"),
    ("Extended Stay", "Extended Stay"),
    ("Red Roof", "Red Roof"),
    ("Choice Hotels", "Choice"),
    ("Comfort Inn", "Choice"),
    ("Quality Inn", "Choice"),
    ("Sleep Inn", "Choice"),
]


def resolve_city(city_or_code: str) -> str:
    """Resolve IATA code to city name. Pass through if not a known code."""
    return IATA_TO_CITY.get(city_or_code.upper(), city_or_code)


def extract_brand(hotel_name: str) -> str:
    """Extract parent chain from hotel name."""
    name_lower = hotel_name.lower()
    for keyword, chain in BRAND_MAP:
        if keyword.lower() in name_lower:
            return chain
    return ""


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate straight-line distance in miles between two lat/lon points."""
    R = 3958.8
    lat1, lon1, lat2, lon2 = (math.radians(x) for x in [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.asin(math.sqrt(a))


def normalize_serpapi_hotel(raw: dict) -> Hotel:
    """Convert a SerpAPI hotel result to Hotel dataclass."""
    gps = raw.get("gps_coordinates", {})
    return Hotel(
        name=raw.get("name", ""),
        brand=extract_brand(raw.get("name", "")),
        stars=raw.get("extracted_hotel_class"),
        rating=raw.get("overall_rating"),
        reviews=raw.get("reviews"),
        rate_per_night=raw.get("rate_per_night", {}).get("extracted_lowest"),
        total=raw.get("total_rate", {}).get("extracted_lowest"),
        currency=raw.get("rate_per_night", {}).get("currency", "USD"),
        amenities=raw.get("amenities", []),
        url=raw.get("link", ""),
        lat=gps.get("latitude"),
        lon=gps.get("longitude"),
        distance_miles=None,
    )


def normalize_fast_hotel(raw) -> Hotel:
    """Convert a fast-hotels result to Hotel dataclass."""
    return Hotel(
        name=raw.name if hasattr(raw, "name") else str(raw),
        brand=extract_brand(raw.name if hasattr(raw, "name") else ""),
        stars=None,
        rating=raw.rating if hasattr(raw, "rating") else None,
        reviews=None,
        rate_per_night=raw.price if hasattr(raw, "price") else None,
        total=None,
        currency="USD",
        amenities=raw.amenities if hasattr(raw, "amenities") else [],
        url=raw.url if hasattr(raw, "url") else "",
        lat=None,
        lon=None,
        distance_miles=None,
    )


def post_filter(
    hotels: list[Hotel],
    min_price: int | None = None,
    max_price: int | None = None,
    stars: str | None = None,
    brands: str | None = None,
    limit: int | None = None,
    lat: float | None = None,
    lon: float | None = None,
    max_distance: float | None = None,
) -> list[Hotel]:
    """Apply filters that the data source didn't handle natively."""
    filtered = list(hotels)

    # Calculate distance if venue lat/lon provided
    if lat is not None and lon is not None:
        updated = []
        for h in filtered:
            if h.lat is not None and h.lon is not None:
                dist = round(haversine_miles(lat, lon, h.lat, h.lon), 1)
                h = Hotel(
                    name=h.name,
                    brand=h.brand,
                    stars=h.stars,
                    rating=h.rating,
                    reviews=h.reviews,
                    rate_per_night=h.rate_per_night,
                    total=h.total,
                    currency=h.currency,
                    amenities=h.amenities,
                    url=h.url,
                    lat=h.lat,
                    lon=h.lon,
                    distance_miles=dist,
                )
            updated.append(h)
        filtered = updated
        if max_distance is not None:
            filtered = [
                h
                for h in filtered
                if h.distance_miles is not None and h.distance_miles <= max_distance
            ]

    if min_price is not None:
        filtered = [
            h
            for h in filtered
            if h.rate_per_night is not None and h.rate_per_night >= min_price
        ]
    if max_price is not None:
        filtered = [
            h
            for h in filtered
            if h.rate_per_night is not None and h.rate_per_night <= max_price
        ]
    if stars:
        star_set = {int(s) for s in stars.split(",")}
        filtered = [h for h in filtered if h.stars in star_set]
    if brands:
        brand_names = {b.strip().lower() for b in brands.split(",")}
        filtered = [
            h
            for h in filtered
            if h.brand.lower() in brand_names
            or any(b in h.name.lower() for b in brand_names)
        ]
    if limit:
        filtered = filtered[:limit]
    return filtered


def search_serpapi(
    city: str,
    checkin: str,
    checkout: str,
    adults: int = 2,
    sort: str = "price",
    currency: str = "USD",
    min_price: int | None = None,
    max_price: int | None = None,
    stars: str | None = None,
    brands: str | None = None,
) -> list[Hotel]:
    """Search Google Hotels via SerpAPI."""
    try:
        import serpapi
    except ImportError:
        raise RuntimeError("serpapi package not installed")

    api_key = os.environ.get("SERPAPI_KEY")
    if not api_key:
        raise RuntimeError("SERPAPI_KEY not set")

    params = {
        "engine": "google_hotels",
        "q": f"Hotels in {city}",
        "check_in_date": checkin,
        "check_out_date": checkout,
        "adults": adults,
        "currency": currency,
        "gl": "us",
        "hl": "en",
    }
    if sort in SORT_MAP:
        params["sort_by"] = SORT_MAP[sort]
    if min_price is not None:
        params["min_price"] = min_price
    if max_price is not None:
        params["max_price"] = max_price
    if stars:
        params["hotel_class"] = stars
    if brands:
        brand_list = [b.strip().lower() for b in brands.split(",")]
        ids = [str(BRAND_IDS[b]) for b in brand_list if b in BRAND_IDS]
        if ids:
            params["brands"] = ",".join(ids)

    client = serpapi.Client(api_key=api_key)
    results = client.search(params)
    return [normalize_serpapi_hotel(p) for p in results.get("properties", [])]


def search_fast_hotels(
    city: str,
    checkin: str,
    checkout: str,
    adults: int = 2,
    sort: str = "price",
) -> list[Hotel]:
    """Search Google Hotels via fast-hotels library. No API key needed."""
    try:
        from fast_hotels.hotels_impl import HotelData, Guests
        from fast_hotels import get_hotels
    except ImportError:
        raise RuntimeError("fast-hotels package not installed")

    hotel_data = [
        HotelData(checkin_date=checkin, checkout_date=checkout, location=city)
    ]
    guests = Guests(adults=adults, children=0, infants=0)
    sort_by = sort if sort in ("price", "rating") else "rating"
    result = get_hotels(
        hotel_data=hotel_data, guests=guests, sort_by=sort_by, fetch_mode="common"
    )
    return [normalize_fast_hotel(h) for h in result.hotels]


def search(
    city: str,
    checkin: str,
    checkout: str,
    adults: int = 2,
    sort: str = "price",
    currency: str = "USD",
    min_price: int | None = None,
    max_price: int | None = None,
    stars: str | None = None,
    brands: str | None = None,
) -> list[Hotel]:
    """Search hotels. Tries SerpAPI first, falls back to fast-hotels.

    Note: SerpAPI handles some filters natively (min/max_price, stars, brands).
    post_filter() in cli.py re-applies them to catch anything the API missed,
    plus handles distance filtering which SerpAPI doesn't support.
    """
    city = resolve_city(city)

    # Try SerpAPI first
    try:
        return search_serpapi(
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
    except Exception as e:
        json.dump(
            {"warning": f"SerpAPI failed: {e}", "code": "SERPAPI_FAILED"}, sys.stderr
        )

    # Fallback to fast-hotels
    try:
        return search_fast_hotels(
            city=city, checkin=checkin, checkout=checkout, adults=adults, sort=sort
        )
    except Exception as e:
        json.dump(
            {"warning": f"fast-hotels failed: {e}", "code": "FALLBACK_FAILED"},
            sys.stderr,
        )

    return []
