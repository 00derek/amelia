import json
from amelia.models import Flight, FlightLeg, Hotel, SearchResult
from amelia.output import to_json, to_json_str


def test_to_json_flight():
    leg = FlightLeg(
        airline="United",
        flight_number="UA871",
        origin="SFO",
        destination="TPE",
        departs="2026-07-01T14:40:00",
        arrives="2026-07-02T18:45:00",
        duration_min=785,
    )
    flight = Flight(price=732, duration_min=785, stops=0, legs=[leg])
    result = to_json(flight)
    assert result["price"] == 732
    assert result["legs"][0]["airline"] == "United"


def test_to_json_list():
    hotels = [
        Hotel(
            name="Test",
            brand="Marriott",
            stars=3,
            rating=4.0,
            reviews=100,
            rate_per_night=150,
            total=600,
            currency="USD",
            amenities=["wifi"],
            url="https://test.com",
            lat=25.0,
            lon=121.5,
            distance_miles=1.0,
        ),
    ]
    result = to_json(hotels)
    assert isinstance(result, list)
    assert result[0]["name"] == "Test"


def test_to_json_str():
    leg = FlightLeg(
        airline="Delta",
        flight_number="DL100",
        origin="JFK",
        destination="LHR",
        departs="2026-07-01T20:00:00",
        arrives="2026-07-02T08:00:00",
        duration_min=420,
    )
    flight = Flight(price=500, duration_min=420, stops=0, legs=[leg])
    json_str = to_json_str([flight])
    parsed = json.loads(json_str)
    assert len(parsed) == 1
    assert parsed[0]["price"] == 500


def test_to_json_search_result():
    result = SearchResult(data=[], rate_limit_remaining=950, empty=True, error=None)
    output = to_json(result)
    assert output["empty"] is True
    assert output["rate_limit_remaining"] == 950
