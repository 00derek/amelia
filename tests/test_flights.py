import os
import sys
from unittest.mock import patch, MagicMock
from amelia.flights import flight_to_model, get_price_insights


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


def _mock_serpapi(search_results):
    """Helper: create a mock serpapi module with given search results."""
    mock_mod = MagicMock()
    mock_client = MagicMock()
    mock_mod.Client.return_value = mock_client
    if isinstance(search_results, list):
        mock_client.search.side_effect = search_results
    else:
        mock_client.search.return_value = search_results
    return mock_mod


@patch.dict("os.environ", {"SERPAPI_KEY": "test-key"})
def test_get_price_insights_success():
    mock_mod = _mock_serpapi(
        {
            "price_insights": {
                "lowest_price": 1403,
                "price_level": "low",
                "typical_price_range": [1800, 4500],
                "price_history": [[1710000000, 2100]],
            }
        }
    )
    sys.modules["serpapi"] = mock_mod
    result = get_price_insights("SFO", "GRU", "2026-07-18", "business")
    assert result.signal == "BUY"
    assert result.lowest_price == 1403
    assert result.typical_range_low == 1800
    assert result.cabin == "business"
    assert result.cabin_fallback is None


@patch.dict("os.environ", {"SERPAPI_KEY": "test-key"})
def test_get_price_insights_no_data_falls_back_to_economy():
    mock_mod = _mock_serpapi(
        [
            {},
            {
                "price_insights": {
                    "lowest_price": 500,
                    "price_level": "typical",
                    "typical_price_range": [400, 800],
                    "price_history": [],
                }
            },
        ]
    )
    sys.modules["serpapi"] = mock_mod
    result = get_price_insights("SFO", "GRU", "2026-07-18", "business")
    assert result.cabin_fallback == "economy"
    assert result.signal == "WAIT"
    assert result.lowest_price == 500


@patch.dict("os.environ", {"SERPAPI_KEY": "test-key"})
def test_get_price_insights_no_data_both_cabins():
    mock_mod = _mock_serpapi([{}, {}])
    sys.modules["serpapi"] = mock_mod
    result = get_price_insights("SFO", "GRU", "2026-07-18", "business")
    assert result.signal == "NO_DATA"
    assert result.cabin_fallback == "economy"


@patch.dict("os.environ", {"SERPAPI_KEY": "test-key"})
def test_get_price_insights_economy_no_fallback():
    """When cabin is already economy and no data, cabin_fallback is None."""
    mock_mod = _mock_serpapi({})
    sys.modules["serpapi"] = mock_mod
    result = get_price_insights("SFO", "GRU", "2026-07-18", "economy")
    assert result.signal == "NO_DATA"
    assert result.cabin_fallback is None


@patch.dict("os.environ", {"SERPAPI_KEY": "test-key"})
def test_get_price_insights_price_level_only():
    """SerpAPI returns price_level but no lowest_price or range — still useful."""
    mock_mod = _mock_serpapi({"price_insights": {"price_level": "high"}})
    sys.modules["serpapi"] = mock_mod
    result = get_price_insights("SFO", "GRU", "2026-07-18", "business")
    assert result.signal == "HIGH"
    assert result.lowest_price is None


def test_get_price_insights_no_api_key():
    with patch.dict("os.environ", {}, clear=True):
        try:
            get_price_insights("SFO", "GRU", "2026-07-18", "business")
            assert False, "Should have raised RuntimeError"
        except RuntimeError as e:
            assert "SERPAPI_KEY" in str(e)
