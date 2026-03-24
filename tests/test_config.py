import tempfile
from pathlib import Path
from amelia.config import (
    parse_config,
    resolve_config,
    bootstrap_amelia_dir,
    DEFAULT_CONFIG,
)


def test_parse_config_global_defaults():
    config_text = """# Travel Config

## Global Defaults
- home_airport: SFO
- travelers: 2
- stops: 0
- cabin: economy
- auto_widen_days: 3
- award_search: false
- hotel_min_price: 90
- hotel_max_price: 200
- hotel_stars: 2,3
- hotel_limit: 5
"""
    config = parse_config(config_text)
    assert config["global"]["home_airport"] == "SFO"
    assert config["global"]["travelers"] == "2"
    assert config["global"]["stops"] == "0"
    assert config["global"]["cabin"] == "economy"


def test_parse_config_profiles():
    config_text = """## Profiles

### tournament
- cabin: economy
- stops: 0
- outbound_day: friday

### international-leisure
- cabin: business
- stops: any
- award_search: true
"""
    config = parse_config(config_text)
    assert config["profiles"]["tournament"]["cabin"] == "economy"
    assert config["profiles"]["international-leisure"]["cabin"] == "business"


def test_parse_config_active_sources():
    config_text = """## Active Sources
- hotels: [marriott, hyatt, ihg, hilton]
- cars: [avis]
"""
    config = parse_config(config_text)
    assert "marriott" in config["active_sources"]["hotels"]


def test_resolve_config_profile_overrides_global():
    config_text = """## Global Defaults
- cabin: economy
- stops: 0

## Profiles

### tournament
- cabin: economy
- stops: 0

### international-leisure
- cabin: business
- stops: any
"""
    config = parse_config(config_text)
    resolved = resolve_config(config, profile="international-leisure")
    assert resolved["cabin"] == "business"
    assert resolved["stops"] == "any"


def test_resolve_config_cli_overrides_all():
    config_text = """## Global Defaults
- cabin: economy

## Profiles

### tournament
- cabin: economy
"""
    config = parse_config(config_text)
    resolved = resolve_config(
        config, profile="tournament", overrides={"cabin": "first"}
    )
    assert resolved["cabin"] == "first"


def test_bootstrap_creates_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        amelia_dir = Path(tmpdir) / ".amelia"
        bootstrap_amelia_dir(amelia_dir)
        assert (amelia_dir / "config.md").exists()
        assert (amelia_dir / "trips").is_dir()
        assert (amelia_dir / "trip-index.json").exists()


def test_default_config_is_valid():
    config = parse_config(DEFAULT_CONFIG)
    assert "global" in config
    assert config["global"]["home_airport"] == "SFO"


def test_parse_config_strips_quotes():
    config_text = """## Global Defaults
- outbound_time: "15:00-23:00"
- name: 'test'
"""
    config = parse_config(config_text)
    assert config["global"]["outbound_time"] == "15:00-23:00"
    assert config["global"]["name"] == "test"
