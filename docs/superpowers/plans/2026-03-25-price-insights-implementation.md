# Price Insights Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Google Flights Price Insights to Amelia CLI so users can see buy/wait/high signals per route during trip checks.

**Architecture:** New `get_price_insights()` function in flights.py calls SerpAPI Google Flights engine, returns a `PriceInsight` dataclass. New CLI command `amelia flights insights` exposes it. Trip skill calls it sequentially after searches.

**Tech Stack:** Python, SerpAPI (existing dep), Click (existing)

**Spec:** `docs/superpowers/specs/2026-03-25-price-insights-design.md`

**Repo:** `/Users/derek/repo/amelia`

---

## File Map

### Modify

```
src/amelia/models.py       — Add PriceInsight dataclass
src/amelia/flights.py      — Add SERPAPI_CABIN_MAP, derive_signal(), get_price_insights()
src/amelia/cli.py           — Add `flights insights` Click command
skills/trip/SKILL.md        — Add price insights dispatch + Price Signals section
```

### Create

```
tests/test_price_signals.py — Signal derivation tests (all 5 branches + edge cases)
```

### Modify (tests)

```
tests/test_flights.py       — Tests for get_price_insights() with mocked SerpAPI
tests/test_cli.py           — Test for `flights insights --help`
```

---

### Task 1: PriceInsight Dataclass

**Files:**
- Modify: `src/amelia/models.py`
- Test: `tests/test_models.py`

- [ ] **Step 1: Write failing test**

Append to `tests/test_models.py`:
```python
def test_price_insight_creation():
    from amelia.models import PriceInsight
    insight = PriceInsight(
        origin="SFO", destination="GRU", date="2026-07-18",
        cabin="business", cabin_fallback=None,
        lowest_price=1403, price_level="low",
        typical_range_low=1800, typical_range_high=4500,
        price_history=[[1710000000, 2100], [1711000000, 1900]],
        signal="BUY",
    )
    assert insight.signal == "BUY"
    assert insight.typical_range_low == 1800


def test_price_insight_no_data():
    from amelia.models import PriceInsight
    insight = PriceInsight(
        origin="SFO", destination="GRU", date="2026-07-18",
        cabin="business", cabin_fallback="economy",
        lowest_price=None, price_level=None,
        typical_range_low=None, typical_range_high=None,
        price_history=[], signal="NO_DATA",
    )
    assert insight.signal == "NO_DATA"
    assert insight.cabin_fallback == "economy"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/derek/repo/amelia && uv run python -m pytest tests/test_models.py::test_price_insight_creation -v`
Expected: FAIL — `PriceInsight` does not exist.

- [ ] **Step 3: Add PriceInsight to models.py**

Append to `src/amelia/models.py` after the `SearchResult` class:

```python
@dataclass
class PriceInsight:
    origin: str
    destination: str
    date: str
    cabin: str
    cabin_fallback: str | None
    lowest_price: int | None
    price_level: str | None
    typical_range_low: int | None
    typical_range_high: int | None
    price_history: list[list[int]]  # [[unix_timestamp, price_usd], ...]
    signal: str  # BUY, GOOD, WAIT, HIGH, NO_DATA
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/derek/repo/amelia && uv run python -m pytest tests/test_models.py -v`
Expected: All tests PASS (including the 2 new ones).

- [ ] **Step 5: Commit**

```bash
cd /Users/derek/repo/amelia && git add src/amelia/models.py tests/test_models.py
git commit -m "feat: add PriceInsight dataclass"
```

---

### Task 2: Signal Derivation Logic

**Files:**
- Modify: `src/amelia/flights.py`
- Create: `tests/test_price_signals.py`

- [ ] **Step 1: Write failing tests for all signal branches**

Create `tests/test_price_signals.py`:

```python
from amelia.flights import derive_signal


def test_buy_signal():
    """Price below typical range low → BUY."""
    assert derive_signal(lowest_price=1403, price_level="low",
                         typical_range_low=1800, typical_range_high=4500) == "BUY"


def test_buy_signal_at_boundary():
    """Price exactly at typical range low → BUY."""
    assert derive_signal(lowest_price=1800, price_level="low",
                         typical_range_low=1800, typical_range_high=4500) == "BUY"


def test_good_signal():
    """Price within range but price_level is low → GOOD."""
    assert derive_signal(lowest_price=2000, price_level="low",
                         typical_range_low=1800, typical_range_high=4500) == "GOOD"


def test_wait_signal():
    """price_level typical → WAIT."""
    assert derive_signal(lowest_price=3000, price_level="typical",
                         typical_range_low=1800, typical_range_high=4500) == "WAIT"


def test_high_signal():
    """price_level high → HIGH."""
    assert derive_signal(lowest_price=5000, price_level="high",
                         typical_range_low=1800, typical_range_high=4500) == "HIGH"


def test_no_typical_range_low():
    """No typical_range but price_level present → use price_level only."""
    assert derive_signal(lowest_price=1000, price_level="low",
                         typical_range_low=None, typical_range_high=None) == "GOOD"


def test_no_typical_range_typical():
    assert derive_signal(lowest_price=1000, price_level="typical",
                         typical_range_low=None, typical_range_high=None) == "WAIT"


def test_no_typical_range_high():
    assert derive_signal(lowest_price=5000, price_level="high",
                         typical_range_low=None, typical_range_high=None) == "HIGH"


def test_no_data():
    """Neither typical_range nor price_level → NO_DATA."""
    assert derive_signal(lowest_price=None, price_level=None,
                         typical_range_low=None, typical_range_high=None) == "NO_DATA"


def test_no_data_price_only():
    """Has lowest_price but no level or range → NO_DATA."""
    assert derive_signal(lowest_price=1500, price_level=None,
                         typical_range_low=None, typical_range_high=None) == "NO_DATA"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/derek/repo/amelia && uv run python -m pytest tests/test_price_signals.py -v`
Expected: FAIL — `derive_signal` does not exist.

- [ ] **Step 3: Implement derive_signal()**

Add to `src/amelia/flights.py` after the `SORT_MAP` dict:

```python
SERPAPI_CABIN_MAP = {
    "economy": 1,
    "premium_economy": 2,
    "business": 3,
    "first": 4,
}


def derive_signal(
    lowest_price: int | None,
    price_level: str | None,
    typical_range_low: int | None,
    typical_range_high: int | None,
) -> str:
    """Derive buy/wait signal from price insights data.

    Returns: BUY, GOOD, WAIT, HIGH, or NO_DATA.
    """
    has_range = typical_range_low is not None and typical_range_high is not None
    has_level = price_level is not None

    if has_range and lowest_price is not None:
        if lowest_price <= typical_range_low:
            return "BUY"
        if price_level == "low":
            return "GOOD"
        if price_level == "high":
            return "HIGH"
        return "WAIT"

    if has_level:
        if price_level == "low":
            return "GOOD"
        if price_level == "high":
            return "HIGH"
        return "WAIT"

    return "NO_DATA"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/derek/repo/amelia && uv run python -m pytest tests/test_price_signals.py -v`
Expected: All 10 tests PASS.

- [ ] **Step 5: Commit**

```bash
cd /Users/derek/repo/amelia && git add src/amelia/flights.py tests/test_price_signals.py
git commit -m "feat: add signal derivation logic for price insights"
```

---

### Task 3: get_price_insights() Function

**Files:**
- Modify: `src/amelia/flights.py`
- Modify: `tests/test_flights.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_flights.py`:

```python
from unittest.mock import patch, MagicMock
from amelia.flights import get_price_insights


@patch("amelia.flights.serpapi")
def test_get_price_insights_success(mock_serpapi):
    mock_client = MagicMock()
    mock_serpapi.Client.return_value = mock_client
    mock_client.search.return_value = {
        "price_insights": {
            "lowest_price": 1403,
            "price_level": "low",
            "typical_price_range": [1800, 4500],
            "price_history": [[1710000000, 2100]],
        }
    }
    with patch.dict("os.environ", {"SERPAPI_KEY": "test-key"}):
        result = get_price_insights("SFO", "GRU", "2026-07-18", "business")
    assert result.signal == "BUY"
    assert result.lowest_price == 1403
    assert result.typical_range_low == 1800
    assert result.cabin == "business"
    assert result.cabin_fallback is None


@patch("amelia.flights.serpapi")
def test_get_price_insights_no_data_falls_back_to_economy(mock_serpapi):
    mock_client = MagicMock()
    mock_serpapi.Client.return_value = mock_client
    # First call (business) returns no insights, second (economy) returns data
    mock_client.search.side_effect = [
        {},  # no price_insights key
        {
            "price_insights": {
                "lowest_price": 500,
                "price_level": "typical",
                "typical_price_range": [400, 800],
                "price_history": [],
            }
        },
    ]
    with patch.dict("os.environ", {"SERPAPI_KEY": "test-key"}):
        result = get_price_insights("SFO", "GRU", "2026-07-18", "business")
    assert result.cabin_fallback == "economy"
    assert result.signal == "WAIT"
    assert result.lowest_price == 500


@patch("amelia.flights.serpapi")
def test_get_price_insights_no_data_both_cabins(mock_serpapi):
    mock_client = MagicMock()
    mock_serpapi.Client.return_value = mock_client
    mock_client.search.side_effect = [{}, {}]  # neither has insights
    with patch.dict("os.environ", {"SERPAPI_KEY": "test-key"}):
        result = get_price_insights("SFO", "GRU", "2026-07-18", "business")
    assert result.signal == "NO_DATA"
    assert result.cabin_fallback == "economy"


def test_get_price_insights_no_api_key():
    with patch.dict("os.environ", {}, clear=True):
        try:
            get_price_insights("SFO", "GRU", "2026-07-18", "business")
            assert False, "Should have raised RuntimeError"
        except RuntimeError as e:
            assert "SERPAPI_KEY" in str(e)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/derek/repo/amelia && uv run python -m pytest tests/test_flights.py::test_get_price_insights_success -v`
Expected: FAIL — `get_price_insights` does not exist.

- [ ] **Step 3: Implement get_price_insights()**

Add to `src/amelia/flights.py`:

```python
import os

from amelia.models import Flight, FlightLeg, PriceInsight


def get_price_insights(
    origin: str,
    destination: str,
    date: str,
    cabin: str = "economy",
) -> PriceInsight:
    """Get Google Flights price insights via SerpAPI.

    Queries the requested cabin first. If no insights returned, falls back to economy.
    Raises RuntimeError if SERPAPI_KEY is not set.
    """
    try:
        import serpapi as serpapi_module
    except ImportError:
        raise RuntimeError("serpapi package not installed")

    # Make serpapi accessible for mocking
    global serpapi
    serpapi = serpapi_module

    api_key = os.environ.get("SERPAPI_KEY")
    if not api_key:
        raise RuntimeError("SERPAPI_KEY not set")

    return _query_insights(origin, destination, date, cabin, api_key)


def _query_insights(
    origin: str, destination: str, date: str, cabin: str, api_key: str,
) -> PriceInsight:
    """Query SerpAPI for price insights, with cabin fallback."""
    travel_class = SERPAPI_CABIN_MAP.get(cabin.lower(), 1)

    # Try requested cabin
    result = _fetch_insights(origin, destination, date, travel_class, api_key)
    if result is not None:
        return _build_insight(origin, destination, date, cabin, None, result)

    # Fallback to economy if different cabin was requested
    if cabin.lower() != "economy":
        result = _fetch_insights(origin, destination, date, 1, api_key)
        if result is not None:
            return _build_insight(origin, destination, date, cabin, "economy", result)

    # No data at all
    return PriceInsight(
        origin=origin, destination=destination, date=date,
        cabin=cabin, cabin_fallback="economy" if cabin.lower() != "economy" else None,
        lowest_price=None, price_level=None,
        typical_range_low=None, typical_range_high=None,
        price_history=[], signal="NO_DATA",
    )


def _fetch_insights(
    origin: str, destination: str, date: str, travel_class: int, api_key: str,
) -> dict | None:
    """Call SerpAPI Google Flights and return price_insights dict, or None."""
    params = {
        "engine": "google_flights",
        "departure_id": origin,
        "arrival_id": destination,
        "outbound_date": date,
        "type": "2",
        "travel_class": travel_class,
        "adults": 1,
        "currency": "USD",
        "hl": "en",
    }
    client = serpapi.Client(api_key=api_key)
    response = client.search(params)
    insights = response.get("price_insights")
    if not insights or "lowest_price" not in insights:
        return None
    return insights


def _build_insight(
    origin: str, destination: str, date: str,
    cabin: str, cabin_fallback: str | None, raw: dict,
) -> PriceInsight:
    """Build PriceInsight from raw SerpAPI price_insights dict."""
    lowest = raw.get("lowest_price")
    level = raw.get("price_level")
    typical = raw.get("typical_price_range", [])
    range_low = typical[0] if len(typical) >= 2 else None
    range_high = typical[1] if len(typical) >= 2 else None
    history = raw.get("price_history", [])

    signal = derive_signal(lowest, level, range_low, range_high)

    return PriceInsight(
        origin=origin, destination=destination, date=date,
        cabin=cabin, cabin_fallback=cabin_fallback,
        lowest_price=lowest, price_level=level,
        typical_range_low=range_low, typical_range_high=range_high,
        price_history=history, signal=signal,
    )
```

**Important:** Update the import at the top of `flights.py` to include `PriceInsight`:
```python
from amelia.models import Flight, FlightLeg, PriceInsight
```

Also add `serpapi = None` module-level variable after the imports for mock support:
```python
serpapi = None  # set by get_price_insights() for testability
```

- [ ] **Step 4: Run all flights tests**

Run: `cd /Users/derek/repo/amelia && uv run python -m pytest tests/test_flights.py -v`
Expected: All tests PASS (2 original + 4 new).

- [ ] **Step 5: Commit**

```bash
cd /Users/derek/repo/amelia && git add src/amelia/flights.py tests/test_flights.py
git commit -m "feat: add get_price_insights() with SerpAPI integration"
```

---

### Task 4: CLI Command

**Files:**
- Modify: `src/amelia/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Write failing test**

Append to `tests/test_cli.py`:

```python
def test_flights_insights_help():
    runner = CliRunner()
    result = runner.invoke(main, ["flights", "insights", "--help"])
    assert result.exit_code == 0
    assert "--from" in result.output
    assert "--to" in result.output
    assert "--date" in result.output
    assert "--cabin" in result.output
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/derek/repo/amelia && uv run python -m pytest tests/test_cli.py::test_flights_insights_help -v`
Expected: FAIL — no such command `insights`.

- [ ] **Step 3: Add insights command to cli.py**

Add after the `flights_search` function in `src/amelia/cli.py`:

```python
@flights.command("insights")
@click.option("--from", "origin", required=True, help="Origin IATA code")
@click.option("--to", "destination", required=True, help="Destination IATA code")
@click.option("--date", required=True, help="Departure date YYYY-MM-DD")
@click.option(
    "--cabin", default="economy", help="economy, premium_economy, business, first"
)
def flights_insights(origin, destination, date, cabin):
    """Get price insights — is now a good time to buy?"""
    from amelia.flights import get_price_insights

    try:
        result = get_price_insights(
            origin=origin, destination=destination, date=date, cabin=cabin,
        )
    except RuntimeError as e:
        if "SERPAPI_KEY" in str(e):
            _error(str(e), "AUTH_MISSING", exit_code=2)
        else:
            _error(str(e), "SEARCH_ERROR")

    print(to_json_str(to_json(result)))
```

- [ ] **Step 4: Run all CLI tests**

Run: `cd /Users/derek/repo/amelia && uv run python -m pytest tests/test_cli.py -v`
Expected: All tests PASS (6 original + 1 new).

- [ ] **Step 5: Commit**

```bash
cd /Users/derek/repo/amelia && git add src/amelia/cli.py tests/test_cli.py
git commit -m "feat: add 'amelia flights insights' CLI command"
```

---

### Task 5: Trip Skill Update

**Files:**
- Modify: `skills/trip/SKILL.md`

- [ ] **Step 1: Add Price Insights section to trip skill**

In `skills/trip/SKILL.md`, add a new step between "Step 6: Collect Results and Write Files" and "Step 7: Generate summary.md". The new step becomes **Step 7: Run Price Insights** and the subsequent steps renumber.

Add this content:

```markdown
### Step 7: Run Price Insights

After all search subagents return, run price insights **sequentially** (not via subagent) for each route. Use the `amelia flights insights` CLI command directly via Bash:

For each route in `trip.json.routes`:

```bash
{AMELIA_CMD} flights insights \
  --from {route.from} --to {route.to} --date {route.date} \
  --cabin {cabin_for_leg}
```

Where `cabin_for_leg` is:
- The trip's configured cabin for international legs (direction == "outbound" or "return")
- `economy` for domestic legs (direction == "domestic")

Parse the JSON output. Collect all results into a Price Signals table.

Append to `~/.amelia/trips/{alias}/price-signals.md`:

```markdown
---

## Run: {YYYY-MM-DD}

| Leg | Price | Typical Range | Level | Signal |
|-----|-------|---------------|-------|--------|
| {origin}→{dest} | ${lowest_price} | ${range_low}–${range_high} | {price_level} | {signal} |
```

If previous entries exist in `price-signals.md`, compare signals and note changes (e.g., "SFO→GRU was WAIT, now BUY").
```

Also add a **Price Signals** section to the summary.md template in Step 8 (formerly Step 7):

```markdown
## Price Signals

| Leg | Current Best | Typical Range | Level | Signal |
|-----|-------------|---------------|-------|--------|
| {origin}→{dest} ({cabin}) | ${lowest_price} | ${range_low}–${range_high} | {price_level} | **{signal}** |
```

- [ ] **Step 2: Verify skill file is valid markdown**

Read through the updated file to ensure formatting is correct and all step numbers are sequential.

- [ ] **Step 3: Commit**

```bash
cd /Users/derek/repo/amelia && git add skills/trip/SKILL.md
git commit -m "feat: add price insights dispatch to trip skill"
```

---

### Task 6: Full Test Suite + Smoke Test

**Files:** All test files

- [ ] **Step 1: Run full test suite**

Run: `cd /Users/derek/repo/amelia && uv run python -m pytest tests/ -v`
Expected: All tests PASS.

- [ ] **Step 2: CLI smoke test**

Run: `cd /Users/derek/repo/amelia && uv run amelia flights insights --help`
Expected: Shows help with --from, --to, --date, --cabin options.

- [ ] **Step 3: Commit and tag**

```bash
cd /Users/derek/repo/amelia && git tag v0.2.0
```
