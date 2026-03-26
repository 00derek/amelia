# Price Insights — Amelia Feature Spec

**Date:** 2026-03-25
**Status:** Design approved, pending implementation plan

## Overview

Add price intelligence to Amelia using Google Flights Price Insights via SerpAPI. A new CLI command (`amelia flights insights`) queries whether the current price for a route is low/typical/high relative to historical norms. The trip skill integrates this into `/trip check` to produce buy/wait signals per leg.

## Goals

- Know if the current price is a good deal or overpriced
- Track price signals over time in trip logs
- No new API keys — reuses existing `SERPAPI_KEY` (same as hotel search)
- Scheduling is user-configured via `/schedule`, not built into the plugin

## CLI Command

```
amelia flights insights --from SFO --to GRU --date 2026-07-18 [--cabin business]
```

**Output (JSON to stdout):**
```json
{
  "origin": "SFO",
  "destination": "GRU",
  "date": "2026-07-18",
  "cabin": "business",
  "cabin_fallback": null,
  "lowest_price": 1403,
  "price_level": "low",
  "typical_range_low": 1800,
  "typical_range_high": 4500,
  "price_history": [[1710000000, 2100], [1711000000, 1900]],
  "signal": "BUY"
}
```

**Cabin fallback:** If SerpAPI returns no price insights for the requested cabin (e.g., business), retry with economy. Set `"cabin_fallback": "economy"` in output so the skill knows the data is approximate.

**Signal derivation:**
- `BUY` — `lowest_price` <= `typical_range_low`
- `GOOD` — `price_level` == "low" but price is above typical_range_low
- `WAIT` — `price_level` == "typical"
- `HIGH` — `price_level` == "high"
- `NO_DATA` — SerpAPI returned no price insights for this route/cabin (even after fallback)

**Exit codes:** Same as other commands (0=success, 1=bad request, 2=auth error, 4=network error).

## SerpAPI Integration

Uses the existing SerpAPI Google Flights engine (`engine=google_flights`). Key parameters:

```python
params = {
    "engine": "google_flights",
    "departure_id": origin,       # IATA code
    "arrival_id": destination,     # IATA code
    "outbound_date": date,         # YYYY-MM-DD
    "type": "2",                   # 1=round-trip, 2=one-way
    "travel_class": 2,             # 1=economy, 2=premium_economy, 3=business, 4=first
    "adults": 1,
    "currency": "USD",
    "hl": "en",
}
```

Travel class mapping:
- economy → 1
- premium_economy → 2
- business → 3
- first → 4

Response contains `price_insights` object:
```json
{
  "price_insights": {
    "lowest_price": 1403,
    "price_level": "high",
    "typical_price_range": [1800, 4500],
    "price_history": [[1691013600, 575], [1696197600, 1339]]
  }
}
```

If `price_insights` is missing or empty in the response, the result is `NO_DATA`.

## Data Model

New dataclass in `src/amelia/models.py`:

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
    price_history: list[list[int]]
    signal: str
```

## Trip Skill Integration

### When insights run

During `/trip check`, after all flight/hotel/award searches complete, the trip skill calls `amelia flights insights` for each route in the trip. Domestic legs use economy; international legs use the trip's configured cabin.

### Summary output

A new section in `summary.md`:

```markdown
## Price Signals

| Leg | Current Best | Typical Range | Level | Signal |
|-----|-------------|---------------|-------|--------|
| SFO→GRU (business) | $1,403 | $1,800–$4,500 | low | **BUY** |
| GIG→SFO (business) | $1,406 | $1,700–$4,200 | low | **BUY** |
| GRU→JPA (economy) | $170 | $150–$250 | typical | WAIT |
| JPA→GIG (economy) | $164 | $140–$230 | typical | WAIT |
```

### Logging

Insights are appended to `~/.amelia/trips/{alias}/price-signals.md`:

```markdown
---

## Run: 2026-03-25

| Leg | Price | Typical Range | Level | Signal |
|-----|-------|---------------|-------|--------|
| SFO→GRU | $1,403 | $1,800–$4,500 | low | BUY |
| GIG→SFO | $1,406 | $1,700–$4,200 | low | BUY |
```

The trip skill reads previous entries to note signal changes: "SFO→GRU was WAIT last run, now BUY."

### No changes to standalone skills

`flight-search`, `award-search`, `hotel-search` skills are unchanged. Price insights only run through the trip orchestrator.

## Files Changed

| File | Change |
|------|--------|
| `src/amelia/models.py` | Add `PriceInsight` dataclass |
| `src/amelia/flights.py` | Add `get_price_insights()` function |
| `src/amelia/cli.py` | Add `amelia flights insights` Click command |
| `skills/trip/SKILL.md` | Add insights call after checks, Price Signals section |
| `tests/test_flights.py` | Tests for `get_price_insights()` |
| `tests/test_cli.py` | Test for `flights insights --help` |

**Not changed:** `awards.py`, `hotels.py`, `config.py`, `output.py`, other skills.

## Daily Monitoring (User-Configured)

Not built into the plugin. Users can optionally set up via Claude Code:

```
/schedule create --cron "0 8 * * *" --prompt "Run /amelia:trip check brazil"
```

This runs the full check (flights + awards + hotels + insights) daily, building price history passively. The trip skill surfaces signal changes in the summary.
