from amelia.hotels import (
    resolve_city,
    extract_brand,
    normalize_serpapi_hotel,
    haversine_miles,
    post_filter,
)
from amelia.models import Hotel


def test_resolve_city_iata():
    assert resolve_city("SFO") == "San Francisco"
    assert resolve_city("TPE") == "Taipei"
    assert resolve_city("GRU") == "Sao Paulo"


def test_resolve_city_passthrough():
    assert resolve_city("Taipei") == "Taipei"
    assert resolve_city("some random city") == "some random city"


def test_extract_brand_marriott_sub():
    assert extract_brand("Courtyard by Marriott Taipei") == "Marriott"
    assert extract_brand("Westin Resort & Spa") == "Marriott"
    assert extract_brand("Sheraton Grand Taipei") == "Marriott"


def test_extract_brand_hyatt():
    assert extract_brand("Hyatt Regency Taipei") == "Hyatt"
    assert extract_brand("Grand Hyatt Taipei") == "Hyatt"


def test_extract_brand_unknown():
    assert extract_brand("Random Boutique Hotel") == ""


def test_normalize_serpapi_hotel():
    raw = {
        "name": "Courtyard by Marriott Taipei",
        "extracted_hotel_class": 3,
        "overall_rating": 4.2,
        "reviews": 500,
        "rate_per_night": {"extracted_lowest": 145, "currency": "USD"},
        "total_rate": {"extracted_lowest": 580},
        "amenities": ["wifi", "pool"],
        "link": "https://example.com",
        "gps_coordinates": {"latitude": 25.0, "longitude": 121.5},
    }
    hotel = normalize_serpapi_hotel(raw)
    assert hotel.name == "Courtyard by Marriott Taipei"
    assert hotel.brand == "Marriott"
    assert hotel.stars == 3
    assert hotel.rate_per_night == 145
    assert hotel.lat == 25.0


def test_haversine_miles():
    # SFO to LAX ~340 miles
    dist = haversine_miles(37.6213, -122.3790, 33.9425, -118.4081)
    assert 330 < dist < 350


def test_post_filter_price():
    hotels = [
        Hotel(
            name="A",
            brand="",
            stars=3,
            rating=4.0,
            reviews=100,
            rate_per_night=100,
            total=400,
            currency="USD",
            amenities=[],
            url="",
            lat=None,
            lon=None,
            distance_miles=None,
        ),
        Hotel(
            name="B",
            brand="",
            stars=3,
            rating=4.0,
            reviews=100,
            rate_per_night=250,
            total=1000,
            currency="USD",
            amenities=[],
            url="",
            lat=None,
            lon=None,
            distance_miles=None,
        ),
    ]
    result = post_filter(hotels, min_price=90, max_price=200)
    assert len(result) == 1
    assert result[0].name == "A"


def test_post_filter_brands():
    hotels = [
        Hotel(
            name="Courtyard Taipei",
            brand="Marriott",
            stars=3,
            rating=4.0,
            reviews=100,
            rate_per_night=150,
            total=600,
            currency="USD",
            amenities=[],
            url="",
            lat=None,
            lon=None,
            distance_miles=None,
        ),
        Hotel(
            name="Random Hotel",
            brand="",
            stars=3,
            rating=4.0,
            reviews=100,
            rate_per_night=150,
            total=600,
            currency="USD",
            amenities=[],
            url="",
            lat=None,
            lon=None,
            distance_miles=None,
        ),
    ]
    result = post_filter(hotels, brands="marriott")
    assert len(result) == 1
    assert result[0].brand == "Marriott"


def test_post_filter_distance():
    hotels = [
        Hotel(
            name="Near",
            brand="",
            stars=3,
            rating=4.0,
            reviews=100,
            rate_per_night=100,
            total=400,
            currency="USD",
            amenities=[],
            url="",
            lat=25.033,
            lon=121.565,
            distance_miles=None,
        ),
        Hotel(
            name="Far",
            brand="",
            stars=3,
            rating=4.0,
            reviews=100,
            rate_per_night=100,
            total=400,
            currency="USD",
            amenities=[],
            url="",
            lat=25.1,
            lon=121.7,
            distance_miles=None,
        ),
    ]
    result = post_filter(hotels, lat=25.033, lon=121.565, max_distance=1.0)
    assert len(result) == 1
    assert result[0].name == "Near"
