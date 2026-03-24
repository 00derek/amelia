from amelia.models import (
    Flight,
    FlightLeg,
    Availability,
    CabinAvailability,
    TripDetail,
    FlightSegment,
    BookingLink,
    LiveResult,
    Route,
    Hotel,
    SearchResult,
)


def test_flight_creation():
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
    assert flight.price == 732
    assert flight.legs[0].airline == "United"


def test_availability_creation():
    cabin = CabinAvailability(
        available=True,
        miles=37500,
        seats=9,
        airlines="JX",
        direct=False,
    )
    avail = Availability(
        id="abc123",
        origin="SFO",
        destination="TPE",
        date="2026-07-01",
        source="alaska",
        cabins={"Y": cabin},
    )
    assert avail.cabins["Y"].miles == 37500


def test_search_result_empty():
    result = SearchResult(data=[], rate_limit_remaining=950, empty=True, error=None)
    assert result.empty is True
    assert result.error is None


def test_search_result_error():
    result = SearchResult(
        data=[], rate_limit_remaining=None, empty=False, error="Auth failed"
    )
    assert result.error == "Auth failed"


def test_hotel_creation():
    hotel = Hotel(
        name="Courtyard Taipei",
        brand="Marriott",
        stars=3,
        rating=4.2,
        reviews=500,
        rate_per_night=145,
        total=580,
        currency="USD",
        amenities=["wifi", "pool"],
        url="https://example.com",
        lat=25.0,
        lon=121.5,
        distance_miles=2.1,
    )
    assert hotel.brand == "Marriott"
    assert hotel.distance_miles == 2.1


def test_trip_detail_creation():
    seg = FlightSegment(
        flight_number="UA871",
        aircraft="Boeing 787-9",
        aircraft_code="789",
        fare_class="X",
        origin="SFO",
        destination="TPE",
        departs="2026-07-01T14:40:00",
        arrives="2026-07-02T18:45:00",
        distance=6450,
        order=0,
    )
    link = BookingLink(label="United.com", url="https://united.com", primary=True)
    trip = TripDetail(
        id="trip1",
        availability_id="avail1",
        segments=[seg],
        duration_min=785,
        stops=0,
        carriers="UA",
        cabin="economy",
        miles=37500,
        taxes=24,
        taxes_currency="USD",
        booking_links=[link],
    )
    assert trip.miles == 37500
    assert trip.booking_links[0].primary is True


def test_live_result_creation():
    seg = FlightSegment(
        flight_number="QF1",
        aircraft="Airbus A380",
        aircraft_code="388",
        fare_class="D",
        origin="SYD",
        destination="SIN",
        departs="2026-07-01T10:00:00",
        arrives="2026-07-01T16:00:00",
        distance=3900,
        order=0,
    )
    live = LiveResult(
        id="live1",
        segments=[seg],
        duration_min=480,
        stops=0,
        carriers="QF",
        cabin="business",
        miles=70000,
        taxes=150,
        taxes_currency="AUD",
        seats=4,
        filtered=False,
    )
    assert live.seats == 4


def test_route_creation():
    route = Route(
        id="route1",
        origin="SFO",
        destination="TPE",
        origin_region="North America",
        destination_region="Asia",
        distance=6450,
        source="united",
    )
    assert route.origin_region == "North America"
