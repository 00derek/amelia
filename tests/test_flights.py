from unittest.mock import MagicMock
from amelia.flights import flight_to_model


def _make_mock_leg(
    airline="United",
    flight_number="UA871",
    dep_airport="SFO",
    arr_airport="TPE",
    dep_time="2026-07-01T14:40:00",
    arr_time="2026-07-02T18:45:00",
    duration=785,
):
    leg = MagicMock()
    leg.airline.name = airline
    leg.flight_number = flight_number
    leg.departure_airport.name = dep_airport
    leg.arrival_airport.name = arr_airport
    leg.departure_datetime.isoformat.return_value = dep_time
    leg.arrival_datetime.isoformat.return_value = arr_time
    leg.duration = duration
    return leg


def _make_mock_flight(price=732, duration=785, stops=0, legs=None):
    flight = MagicMock()
    flight.price = price
    flight.duration = duration
    flight.stops = stops
    flight.legs = legs or [_make_mock_leg()]
    return flight


def test_flight_to_model():
    mock_flight = _make_mock_flight()
    result = flight_to_model(mock_flight)
    assert result.price == 732
    assert result.duration_min == 785
    assert result.stops == 0
    assert len(result.legs) == 1
    assert result.legs[0].airline == "United"
    assert result.legs[0].origin == "SFO"


def test_flight_to_model_with_connection():
    leg1 = _make_mock_leg(
        airline="American",
        flight_number="AA100",
        dep_airport="SFO",
        arr_airport="DFW",
        duration=240,
    )
    leg2 = _make_mock_leg(
        airline="American",
        flight_number="AA200",
        dep_airport="DFW",
        arr_airport="GRU",
        duration=600,
    )
    mock_flight = _make_mock_flight(price=478, duration=900, stops=1, legs=[leg1, leg2])
    result = flight_to_model(mock_flight)
    assert result.stops == 1
    assert len(result.legs) == 2
    assert result.legs[0].destination == "DFW"
    assert result.legs[1].origin == "DFW"
