from unittest.mock import patch, MagicMock
from amelia.awards import SeatsAeroClient, PROGRAMS
from amelia.models import TripDetail


def test_programs_returns_list():
    client = SeatsAeroClient(api_key="test-key")
    programs = client.programs()
    assert isinstance(programs, list)
    assert len(programs) == 24
    assert "united" in programs
    assert "aeroplan" in programs


def test_programs_sorted():
    client = SeatsAeroClient(api_key="test-key")
    programs = client.programs()
    assert programs == sorted(programs)


def test_client_headers():
    client = SeatsAeroClient(api_key="my-key-123")
    headers = client._headers()
    assert headers["Partner-Authorization"] == "my-key-123"


def _mock_response(json_data, status_code=200, headers=None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    resp.headers = headers or {}
    return resp


@patch("amelia.awards.requests.get")
def test_routes_success(mock_get):
    mock_get.return_value = _mock_response(
        [
            {
                "ID": "route1",
                "OriginAirport": "SFO",
                "OriginRegion": "North America",
                "DestinationAirport": "TPE",
                "DestinationRegion": "Asia",
                "Distance": 6450,
                "Source": "united",
            },
        ]
    )
    client = SeatsAeroClient(api_key="test-key")
    result = client.routes(source="united")
    assert not result.empty
    assert len(result.data) == 1
    assert result.data[0].origin == "SFO"
    assert result.data[0].destination == "TPE"


@patch("amelia.awards.requests.get")
def test_routes_empty(mock_get):
    mock_get.return_value = _mock_response([])
    client = SeatsAeroClient(api_key="test-key")
    result = client.routes(source="nonexistent")
    assert result.empty
    assert len(result.data) == 0


@patch("amelia.awards.requests.get")
def test_auth_error(mock_get):
    mock_get.return_value = _mock_response(
        {"error": "unauthorized"},
        status_code=401,
    )
    client = SeatsAeroClient(api_key="bad-key")
    result = client.routes(source="united")
    assert result.error is not None
    assert "auth" in result.error.lower() or "401" in result.error


@patch("amelia.awards.requests.get")
def test_rate_limit_remaining(mock_get):
    mock_get.return_value = _mock_response(
        [
            {
                "ID": "r1",
                "OriginAirport": "SFO",
                "OriginRegion": "NA",
                "DestinationAirport": "TPE",
                "DestinationRegion": "Asia",
                "Distance": 6450,
                "Source": "united",
            }
        ],
        headers={"x-ratelimit-remaining": "995"},
    )
    client = SeatsAeroClient(api_key="test-key")
    result = client.routes(source="united")
    assert result.rate_limit_remaining == 995


def _avail_item(
    id="avail1",
    origin="SFO",
    dest="TPE",
    date="2026-07-01",
    source="united",
    y_miles="35000",
    j_miles="70000",
    y_seats=9,
    j_seats=2,
    y_avail=True,
    j_avail=True,
):
    return {
        "ID": id,
        "Route": {
            "OriginAirport": origin,
            "DestinationAirport": dest,
            "OriginRegion": "North America",
            "DestinationRegion": "Asia",
            "Distance": 6450,
            "Source": source,
        },
        "Date": date,
        "YAvailable": y_avail,
        "WAvailable": False,
        "JAvailable": j_avail,
        "FAvailable": False,
        "YMileageCost": y_miles,
        "WMileageCost": "0",
        "JMileageCost": j_miles,
        "FMileageCost": "0",
        "YRemainingSeats": y_seats,
        "WRemainingSeats": 0,
        "JRemainingSeats": j_seats,
        "FRemainingSeats": 0,
        "YAirlines": "UA",
        "WAirlines": "",
        "JAirlines": "UA",
        "FAirlines": "",
        "YDirect": True,
        "WDirect": False,
        "JDirect": True,
        "FDirect": False,
        "Source": source,
    }


@patch("amelia.awards.requests.get")
def test_search_success(mock_get):
    mock_get.return_value = _mock_response(
        {
            "data": [_avail_item()],
            "count": 1,
            "hasMore": False,
            "cursor": 123,
        }
    )
    client = SeatsAeroClient(api_key="test-key")
    result = client.search(
        origin="SFO", destination="TPE", start_date="2026-07-01", end_date="2026-07-07"
    )
    assert not result.empty
    assert len(result.data) == 1
    avail = result.data[0]
    assert avail.origin == "SFO"
    assert avail.cabins["Y"].miles == 35000
    assert avail.cabins["J"].seats == 2
    assert avail.cabins["W"].available is False


@patch("amelia.awards.requests.get")
def test_search_pagination(mock_get):
    page1 = _mock_response(
        {
            "data": [_avail_item(id=f"a{i}") for i in range(3)],
            "count": 5,
            "hasMore": True,
            "cursor": 100,
        }
    )
    page2 = _mock_response(
        {
            "data": [_avail_item(id=f"b{i}", date="2026-07-02") for i in range(2)],
            "count": 5,
            "hasMore": False,
            "cursor": 200,
        }
    )
    mock_get.side_effect = [page1, page2]
    client = SeatsAeroClient(api_key="test-key")
    result = client.search(
        origin="SFO",
        destination="TPE",
        start_date="2026-07-01",
        end_date="2026-07-07",
        limit=10,
    )
    assert len(result.data) == 5


@patch("amelia.awards.requests.get")
def test_trip_success(mock_get):
    mock_get.return_value = _mock_response(
        {
            "data": [
                {
                    "ID": "trip1",
                    "AvailabilityID": "avail1",
                    "TotalDuration": 785,
                    "Stops": 0,
                    "Carriers": "UA",
                    "RemainingSeats": 9,
                    "MileageCost": 35000,
                    "TotalTaxes": 24,
                    "TaxesCurrency": "USD",
                    "TaxesCurrencySymbol": "$",
                    "FlightNumbers": "UA871",
                    "Cabin": "economy",
                    "DepartsAt": "2026-07-01T14:40:00Z",
                    "ArrivesAt": "2026-07-02T18:45:00Z",
                    "Source": "united",
                    "AvailabilitySegments": [
                        {
                            "ID": "seg1",
                            "FlightNumber": "UA871",
                            "AircraftName": "Boeing 787-9",
                            "AircraftCode": "789",
                            "FareClass": "X",
                            "OriginAirport": "SFO",
                            "DestinationAirport": "TPE",
                            "Distance": 6450,
                            "DepartsAt": "2026-07-01T14:40:00Z",
                            "ArrivesAt": "2026-07-02T18:45:00Z",
                            "Order": 0,
                        }
                    ],
                }
            ],
            "booking_links": [
                {
                    "label": "United.com",
                    "link": "https://united.com/book",
                    "primary": True,
                },
            ],
        }
    )
    client = SeatsAeroClient(api_key="test-key")
    result = client.trip(availability_id="avail1")
    assert not result.error
    trip = result.data
    assert isinstance(trip, TripDetail)
    assert trip.miles == 35000
    assert len(trip.segments) == 1
    assert trip.segments[0].flight_number == "UA871"
    assert len(trip.booking_links) == 1


@patch("amelia.awards.requests.get")
def test_availability_success(mock_get):
    mock_get.return_value = _mock_response(
        {
            "data": [
                _avail_item(
                    id="avail2",
                    origin="SFO",
                    dest="NRT",
                    source="aeroplan",
                    j_miles="55000",
                    j_seats=4,
                )
            ],
            "count": 1,
            "hasMore": False,
            "cursor": 0,
        }
    )
    client = SeatsAeroClient(api_key="test-key")
    result = client.availability(source="aeroplan", cabin="business")
    assert not result.empty
    assert result.data[0].cabins["J"].miles == 55000


@patch("amelia.awards.requests.post")
def test_live_success(mock_post):
    mock_post.return_value = _mock_response(
        {
            "results": [
                {
                    "ID": "live1",
                    "TotalDuration": 600,
                    "Stops": 1,
                    "Carriers": "QF",
                    "RemainingSeats": 2,
                    "MileageCost": 70000,
                    "TotalTaxes": 150,
                    "TaxesCurrency": "USD",
                    "TaxesCurrencySymbol": "$",
                    "FlightNumbers": "QF1,QF11",
                    "Cabin": "business",
                    "DepartsAt": "2026-07-01T10:00:00Z",
                    "ArrivesAt": "2026-07-01T22:00:00Z",
                    "Source": "qantas",
                    "Filtered": False,
                    "AvailabilitySegments": [
                        {
                            "FlightNumber": "QF1",
                            "AircraftName": "A380",
                            "AircraftCode": "388",
                            "FareClass": "D",
                            "OriginAirport": "SYD",
                            "DestinationAirport": "SIN",
                            "DepartsAt": "2026-07-01T10:00:00Z",
                            "ArrivesAt": "2026-07-01T16:00:00Z",
                            "Distance": 3900,
                            "Order": 0,
                        }
                    ],
                }
            ],
        }
    )
    client = SeatsAeroClient(api_key="test-key")
    result = client.live(
        origin="SYD", destination="SIN", date="2026-07-01", source="qantas"
    )
    assert not result.empty
    assert len(result.data) == 1
    assert result.data[0].miles == 70000
    assert result.data[0].cabin == "business"
