---
name: award-search
description: Search for award flight availability using Seats.aero API via amelia CLI. Standalone or dispatched by /trip orchestrator.
---

## Overview

Searches for award flight availability using `amelia awards` commands (Seats.aero Partner API).
Can run standalone (prompts for input) or orchestrated (receives params, returns results).

Each invocation searches **one route, one direction**. The orchestrator handles outbound + return as separate dispatches.

**API key**: `SEATS_AERO_API_KEY` environment variable (Seats.aero Pro key required).

## Available Commands

| Command | Purpose |
|---------|---------|
| `amelia awards search` | Cached search — primary, route-specific |
| `amelia awards trip <id>` | Trip details + booking links for a result |
| `amelia awards availability` | Bulk program availability — fallback |
| `amelia awards live` | Real-time search — most expensive, use sparingly |
| `amelia awards programs` | List available mileage programs |
| `amelia awards routes` | List routes for a specific program |

## Read Config

Before searching, read `~/.amelia/config.md` for defaults (cabin, min_seats, auto_widen_days).

## Input Collection (Standalone Mode)

If invoked directly, use AskUserQuestion to collect:

1. **Origin airport** — default: home_airport from config
2. **Destination airport** — e.g., "TPE"
3. **Date** — center date for search
4. **Date range** (optional) — defaults to ±auto_widen_days from config
5. **Cabin class** — economy, premium, business, first
6. **Minimum seats** — default from config (e.g., 2)
7. **Profile** (optional) — e.g., "international-leisure"

If orchestrator provides these in the prompt, skip AskUserQuestion.

## Search Strategy

### Step 1: Cached Search (Primary)

```bash
amelia awards search \
  --from {origin} --to {destination} \
  --date {start_date} --end-date {end_date} \
  --cabin {cabin} \
  --sort miles \
  --limit 50
```

Parse the JSON output. Filter to results with seats >= min_seats from the cabin-specific data.

### Step 2: Auto-widen (If Zero Results)

If cached search returns empty:
1. Widen date range by ±auto_widen_days
2. Re-run the search with wider dates
3. If still zero, try adding nearby origin airports: `--from {origin},OAK,SJC`
4. Note any widening in the output

### Step 3: Fallback — Bulk Availability

If cached search + widening returns nothing:

```bash
amelia awards availability \
  --source {program} \
  --cabin {cabin} \
  --origin-region "North America" --dest-region "{region}" \
  --start-date {start_date} --end-date {end_date} \
  --limit 30
```

Run for relevant programs: aeroplan, united, alaska, delta.
Filter results for the requested origin/destination pair.

### Step 4: Fallback — Live Search

If bulk availability also returns nothing and user specifically requests real-time data:

```bash
amelia awards live \
  --from {origin} --to {destination} \
  --date {date} --source {program} \
  --seats {min_seats}
```

Note: Live search uses more API quota. Only use when explicitly requested or cached data is clearly stale.

### Step 5: Trip Details (Top Results)

For the top 5 results (after filtering), enrich with routing details:

```bash
amelia awards trip {availability_id}
```

Parse trip details for:
- Actual routing (e.g., SFO→SEA→TPE)
- Airlines and flight numbers per leg
- Departure/arrival times, aircraft type
- Booking links

**Important**: Verify the trip details match the requested origin/destination.

### Step 6: Rank and Cap

- Rank by: exact airport match first, then miles cost ascending
- Cap at top 10 results

## Exploring Routes and Programs

When the user asks about available programs or routes:

```bash
# List all 24 mileage programs
amelia awards programs

# What routes does United have from SFO?
amelia awards routes --source united
```

## Rate Limit Awareness

The Seats.aero API has a 1,000 calls/day limit. The CLI outputs rate limit remaining to stderr as JSON: `{"rate_limit_remaining": 995}`. Check this and warn the user if below 100.

## Output Format

```markdown
### Award Flights: {origin} → {dest} — {start_date} to {end_date}

| # | Date | Program | Miles | Taxes | Cabin | Airline | Route | Stops | Seats |
|---|------|---------|-------|-------|-------|---------|-------|-------|-------|
| 1 | Jun 2 | Alaska | 37,500 | $24 | Y | JX31 | SFO→SEA→TPE | 1 | 9 |
| 2 | Jun 3 | United | 66,400 | $6 | Y | UA871 | SFO→TPE | 0 | 9 |

**Searched**: {timestamp} | **Params**: {cabin}, {min_seats}+ seats, ±{days} days
**Note**: {any caveats about cache gaps, widened search, fallback source, etc.}
```

### If Standalone Mode
Present the table directly to the user.

### If Orchestrated Mode
Return the markdown block as text. Do NOT write to any files.

## Error Handling

- **Exit code 2 (auth error)**: Report "SEATS_AERO_API_KEY not set or invalid."
- **Exit code 3 (rate limited)**: Report "Seats.aero rate limit hit (1,000/day). Try again later."
- **Exit code 4 (network)**: Retry once. If still failing, report error.
- **No results after all fallbacks**: Report "No award availability found" with params used.
