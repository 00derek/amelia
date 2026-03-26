from amelia.flights import derive_signal


def test_buy_signal():
    """Price below typical range low → BUY."""
    assert (
        derive_signal(
            lowest_price=1403,
            price_level="low",
            typical_range_low=1800,
            typical_range_high=4500,
        )
        == "BUY"
    )


def test_buy_signal_at_boundary():
    """Price exactly at typical range low → BUY."""
    assert (
        derive_signal(
            lowest_price=1800,
            price_level="low",
            typical_range_low=1800,
            typical_range_high=4500,
        )
        == "BUY"
    )


def test_good_signal():
    """Price within range but price_level is low → GOOD."""
    assert (
        derive_signal(
            lowest_price=2000,
            price_level="low",
            typical_range_low=1800,
            typical_range_high=4500,
        )
        == "GOOD"
    )


def test_wait_signal():
    """price_level typical → WAIT."""
    assert (
        derive_signal(
            lowest_price=3000,
            price_level="typical",
            typical_range_low=1800,
            typical_range_high=4500,
        )
        == "WAIT"
    )


def test_high_signal():
    """price_level high → HIGH."""
    assert (
        derive_signal(
            lowest_price=5000,
            price_level="high",
            typical_range_low=1800,
            typical_range_high=4500,
        )
        == "HIGH"
    )


def test_no_typical_range_low():
    """No typical_range but price_level present → use price_level only."""
    assert (
        derive_signal(
            lowest_price=1000,
            price_level="low",
            typical_range_low=None,
            typical_range_high=None,
        )
        == "GOOD"
    )


def test_no_typical_range_typical():
    assert (
        derive_signal(
            lowest_price=1000,
            price_level="typical",
            typical_range_low=None,
            typical_range_high=None,
        )
        == "WAIT"
    )


def test_no_typical_range_high():
    assert (
        derive_signal(
            lowest_price=5000,
            price_level="high",
            typical_range_low=None,
            typical_range_high=None,
        )
        == "HIGH"
    )


def test_no_data():
    """Neither typical_range nor price_level → NO_DATA."""
    assert (
        derive_signal(
            lowest_price=None,
            price_level=None,
            typical_range_low=None,
            typical_range_high=None,
        )
        == "NO_DATA"
    )


def test_no_data_price_only():
    """Has lowest_price but no level or range → NO_DATA."""
    assert (
        derive_signal(
            lowest_price=1500,
            price_level=None,
            typical_range_low=None,
            typical_range_high=None,
        )
        == "NO_DATA"
    )
