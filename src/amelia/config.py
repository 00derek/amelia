"""Config parser and bootstrap for ~/.amelia/."""

import json
import re
import sys
from pathlib import Path

AMELIA_DIR = Path.home() / ".amelia"

DEFAULT_CONFIG = """# Amelia Config

## Global Defaults
- home_airport: SFO
- travelers: 2
- stops: 0
- auto_widen_days: 3
- cabin: economy
- award_search: false
- hotel_min_price: 90
- hotel_max_price: 200
- hotel_stars: 2,3
- hotel_limit: 5

## Loyalty Programs
- Marriott: member
- Hyatt: member

## Profiles

### tournament
- outbound_day: friday
- outbound_time: 15:00-23:00
- outbound_arrival_cutoff: 22:00
- return_day: monday
- return_time: 18:00-23:59
- cabin: economy
- stops: 0

### international-leisure
- cabin: business
- stops: any
- min_seats: 2
- auto_widen_days: 5
- award_search: true
- hotel_stars: 4,5
- hotel_max_price: 400

## Active Sources
- hotels: [marriott, hyatt, ihg, hilton]
- cars: [avis]
- rideshare: [uber]
"""


def parse_config(text: str) -> dict:
    """Parse markdown config into structured dict.

    Returns:
        {
            "global": {key: value, ...},
            "profiles": {name: {key: value, ...}, ...},
            "active_sources": {key: [values], ...},
            "loyalty": {key: value, ...},
        }
    """
    config = {"global": {}, "profiles": {}, "active_sources": {}, "loyalty": {}}
    current_section = None
    current_profile = None

    for line in text.splitlines():
        line = line.strip()

        # Section headers
        if line.startswith("### "):
            current_profile = line[4:].strip().lower()
            if current_section == "profiles":
                config["profiles"].setdefault(current_profile, {})
            continue
        if line.startswith("## "):
            header = line[3:].strip().lower()
            if "default" in header:
                current_section = "global"
            elif "profile" in header:
                current_section = "profiles"
            elif "source" in header:
                current_section = "active_sources"
            elif "loyalty" in header:
                current_section = "loyalty"
            else:
                current_section = header
            current_profile = None
            continue

        # Key-value pairs
        match = re.match(r"^- (.+?):\s*(.+)$", line)
        if not match:
            continue

        key = match.group(1).strip().lower()
        value = match.group(2).strip().strip('"').strip("'")  # Strip quotes

        # Parse list values: [a, b, c]
        list_match = re.match(r"^\[(.+)\]$", value)
        if list_match:
            value = [v.strip() for v in list_match.group(1).split(",")]

        if current_section == "global":
            config["global"][key] = value
        elif current_section == "profiles" and current_profile:
            config["profiles"][current_profile][key] = value
        elif current_section == "active_sources":
            config["active_sources"][key] = (
                value if isinstance(value, list) else [value]
            )
        elif current_section == "loyalty":
            config["loyalty"][key] = value

    return config


def resolve_config(
    config: dict,
    profile: str | None = None,
    overrides: dict | None = None,
) -> dict:
    """Resolve config with precedence: overrides > profile > global."""
    resolved = dict(config.get("global", {}))
    if profile and profile in config.get("profiles", {}):
        resolved.update(config["profiles"][profile])
    if overrides:
        resolved.update({k: v for k, v in overrides.items() if v is not None})
    return resolved


def load_config(config_path: Path | None = None) -> dict:
    """Load and parse config from file."""
    path = config_path or (AMELIA_DIR / "config.md")
    if not path.exists():
        return parse_config(DEFAULT_CONFIG)
    return parse_config(path.read_text())


def bootstrap_amelia_dir(amelia_dir: Path | None = None) -> None:
    """Create ~/.amelia/ with default config if it doesn't exist."""
    d = amelia_dir or AMELIA_DIR
    if d.exists():
        return
    d.mkdir(parents=True)
    (d / "trips").mkdir()
    (d / "config.md").write_text(DEFAULT_CONFIG)
    (d / "trip-index.json").write_text(json.dumps({"trips": {}}, indent=2))
    print(f"Created {d}/ — edit config.md for preferences", file=sys.stderr)
