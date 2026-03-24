---
name: flight-search
description: Search for cash flight prices using Google Flights data via amelia CLI. Standalone or dispatched by /trip orchestrator.
---

## Overview

Searches for cash flight prices on a single route using `uv run --directory ${CLAUDE_PLUGIN_ROOT} --env-file ~/.amelia/.env amelia flights search` (Google Flights data).
Can run standalone (prompts for input) or orchestrated (receives params, returns results).

Each invocation searches **one route, one direction**. The orchestrator handles outbound + return as separate dispatches.

## Read Config

Before searching, read `~/.amelia/config.md` for:
- home_airport (default origin)
- cabin, stops defaults
- Profile defaults if a profile name is provided

## Input Collection (Standalone Mode)

If invoked directly (not by orchestrator), use AskUserQuestion to collect:

1. **Origin airport** — default: home_airport from config (SFO)
2. **Destination airport** — e.g., "TPE" or "BOS"
3. **Date** — e.g., "2026-06-03"
4. **Cabin class** — economy (default), premium_economy, business, first
5. **Stops** — 0 for nonstop (default), ANY, 1, 2
6. **Time window** (optional) — e.g., "15-23" for departures 3pm-11pm
7. **Profile** (optional) — e.g., "tournament" to load profile defaults

If orchestrator provides these in the prompt, skip AskUserQuestion and use provided values.

## Search Execution

1. Resolve preferences: profile defaults → global defaults → user overrides (most specific wins)
2. Run the amelia CLI:

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT} --env-file ~/.amelia/.env amelia flights search \
  --from {origin} --to {destination} --date {date} \
  --cabin {cabin} --stops {stops} --sort cheapest \
  [--time {time_window}] [--airlines {airlines}]
```

3. Parse the JSON output from stdout
4. If JSON is empty array `[]`, check stderr for error details

### Auto-widen Logic

If zero results on exact date:
1. Re-search with ±1 day (run date-1 and date+1)
2. If still zero, widen to ±`auto_widen_days` from resolved preferences
3. Note the widened range in output header

### Post-search Filtering

Apply any constraints the CLI doesn't handle natively:
- **Arrival cutoff**: If `outbound_arrival_cutoff` is set (e.g., "22:00"), exclude flights arriving after that time
- Sort/rank remaining results

## Output Format

Format results as a markdown table. The JSON includes per-leg details in the `legs` array — use these to compute layover information.

### Computing layover details

For each flight with `stops > 0`, compute from the `legs` array:
- **Connection cities**: The arrival airport of each leg except the last (use IATA code)
- **Layover duration**: Time between one leg's `arrives` and the next leg's `departs`
- **Per-leg breakdown**: Show as a detail line beneath the main row

### Table format

```markdown
### Cash Flights: {origin} → {dest} — {date}

| # | Airline | Flight | Depart | Arrive | Stops | Duration | Layover | Price |
|---|---------|--------|--------|--------|-------|----------|---------|-------|
| 1 | United | UA871 | 2:40pm | 6:45pm+1 | 0 | 13h 5m | — | $732 |
| 2 | American | AA2387→AA963 | 2:03pm | 9:00am+1 | 1 (DFW) | 14h 57m | 1h 25m DFW | $478 |
| | | *SFO 2:03p→DFW 7:28p (4h 25m) · DFW 8:53p→GRU 9:00a+1 (9h 7m)* | | | | | | |

**Searched**: {timestamp} | **Params**: {cabin}, {stops_desc}, sorted by price
**Timezones**: {origin} ({tz}) · {connection_cities} ({tz}) · {dest} ({tz})
🔗 [View on Google Flights]({google_flights_url})
```

### Timezone reference line

Always include a timezone line listing all unique cities in the results (origin, connections, destination). Format:

```
**Timezones**: SFO (UTC-7 PDT) · DFW (UTC-5 CDT) · GRU (UTC-3 BRT)
```

### Google Flights link

Always include a search link at the bottom:

```
https://www.google.com/travel/flights?q={origin}%20to%20{dest}%20{month_name}%20{day}%20{year}%20{cabin_label}
```

- Use full month name (e.g., `July`, `December`)
- `{cabin_label}`: omit for economy, otherwise `premium%20economy`, `business%20class`, or `first%20class`

### Detail row rules

- **Nonstop flights**: No detail row needed
- **1-stop flights**: One detail row showing both legs with times and durations
- **2-stop flights**: One detail row showing all three legs separated by ` · `
- Use 12h format with am/pm shorthand (e.g., `2:03p`, `9:00a+1`)

### If Standalone Mode
Present the table directly to the user.

### If Orchestrated Mode
Return the markdown block as text. Do NOT write to any files — the orchestrator handles file writing.

## Error Handling

- **No results**: Report "No flights found" with the params used. If auto-widen also found nothing, note that.
- **CLI fails**: Check stderr JSON for error code. Report the error message.
- **Invalid airport code**: Report the parse error.
