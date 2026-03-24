---
name: hotel-search
description: Search for hotel rates via amelia CLI (Google Hotels data). Standalone or dispatched by /trip orchestrator.
---

## Overview

Searches Google Hotels for hotel availability using `amelia hotels search`. Can run standalone (prompts for input) or orchestrated (receives params, returns results).

Each invocation searches one city for one date range. The orchestrator handles dispatch.

## Read Config

Before starting, read `~/.amelia/config.md` for:
- travelers (default adults count)
- Hotel defaults: hotel_min_price, hotel_max_price, hotel_stars, hotel_limit

## Input Collection (Standalone Mode)

If invoked directly (not by orchestrator), use AskUserQuestion to collect:

1. **City** — e.g., "Taipei" or IATA code "TPE"
2. **Check-in date** — e.g., "2026-06-03"
3. **Check-out date** — e.g., "2026-06-07"
4. **Budget** (optional) — default: $hotel_min_price–$hotel_max_price from config
5. **Stars** (optional) — default: hotel_stars from config

If orchestrator provides these, skip AskUserQuestion.

## Search

Run the amelia CLI:

```bash
amelia hotels search \
  --city {city} \
  --checkin {checkin} \
  --checkout {checkout} \
  --adults {travelers} \
  --min-price {hotel_min_price} \
  --max-price {hotel_max_price} \
  --stars {hotel_stars} \
  --brands {active_sources.hotels as comma-separated} \
  --sort price \
  --limit {hotel_limit} \
  --currency USD
```

Parse the JSON output from stdout.

## Output

Format results as a markdown table:

```markdown
### Hotels — {city}

**Check-in**: {checkin} → **Check-out**: {checkout}

| Hotel | Chain | Stars | Rate/Night | Total | Rating | Distance | Link |
|-------|-------|-------|------------|-------|--------|----------|------|
| Courtyard Taipei | Marriott | 3 | $145 | $580 | 4.2 | 2.1 mi | [Marriott](url) |

*For points rates, check [rooms.aero](https://rooms.aero)*
```

### If Standalone Mode

Display the table to the user.

### If Orchestrated Mode

Return the markdown table. Do NOT write files — the orchestrator handles file I/O.

## Error Handling

- **CLI fails**: Check stderr for error JSON. Report which source(s) failed (SerpAPI, fast-hotels, or both).
- **Empty results**: Note "No hotels found matching filters" and suggest widening budget or star range.
- **SERPAPI_KEY not set**: Will fall back to fast-hotels automatically. If both fail, report the error.
