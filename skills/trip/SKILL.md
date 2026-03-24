---
name: trip
description: Create and manage trips. Dispatches flight-search, award-search, and hotel-search skills. Handles trip memory (store, recall, re-run). Standalone orchestrator.
---

## Overview

The `/trip` skill is the orchestrator and memory layer for travel search. It:
- Creates trips with alias-based identity
- Resolves layered preferences (global → profile → trip overrides)
- Dispatches `/flight-search`, `/award-search`, and `/hotel-search` as parallel subagents
- Writes results to per-trip folders (append-only logs)
- Enables "check again" (re-run with stored params) and "recall" (show cached results)

**State directory**: `~/.amelia/` (config, trips, trip-index)

## Usage Patterns

| User says | Action |
|-----------|--------|
| "search SFO to TPE around 7/1 business, 2 pax" | **New trip** → create + search |
| "/trip new SFO TPE 2026-07-01" | **New trip** (explicit) |
| "/trip check TPE" or "TPE trip, check again" | **Check again** → re-run stored params |
| "what did we find for TPE?" or "/trip show TPE" | **Recall** → show cached results |
| "/trip list" | **List** → show all tracked trips |

## Read Config

Before any operation, read:
1. `~/.amelia/config.md` — global defaults and profiles
2. `~/.amelia/trip-index.json` — alias-to-folder mapping

## Mode: New Trip

### Step 1: Parse Input

Extract as much as you can from the user's message. Only ask about what's missing or ambiguous — don't ask about things that have clear defaults in the config or profile.

**CRITICAL: Ask ONE question at a time. Do NOT list multiple questions in a single message. Send one question, wait for the answer, then ask the next if needed. This is not optional — never combine questions.**

**CRITICAL: Use the AskUserQuestion tool for EVERY question.** Do NOT output questions as plain text. AskUserQuestion renders an interactive picker with up/down arrow selection. Always provide selectable options. Examples:

- Return date → AskUserQuestion with options: ["7/27 — 1 week", "7/30 — 10 days", "8/3 — 2 weeks"] and allow free text for custom dates
- Profile → AskUserQuestion with options: ["Yes, use international-leisure (business, awards, 4-5★)", "No, keep defaults"]
- Destination → AskUserQuestion with options: ["NRT — Tokyo Narita", "HND — Tokyo Haneda"] and allow free text for other codes

Ask in this priority order (skip any that are already known or have defaults):
1. **Destination** — only if not provided
2. **Date** — only if not provided (outbound date)
3. **Return date** — only if not provided and not derivable. Suggest durations based on destination (e.g., 1 week, 10 days, 2 weeks)
4. **Profile** — suggest a match if one fits, ask to confirm

Do NOT ask about:
- **Origin** — use home_airport from config
- **Cabin** — use profile/config default
- **Stops** — use profile/config default
- **Min seats** — use profile/config default
- **Routing/connections** — figure this out yourself based on airport connectivity (search each leg separately)
- **Custom alias** — auto-generate from destination, only ask on collision

### Step 2: Generate Alias

1. Default alias: lowercase destination code (e.g., "tpe")
2. Check `~/.amelia/trip-index.json` for collision
3. On collision: suggest `{alias}-2` or `{alias}-{month}` and ask user to confirm

The alias IS the folder name (e.g., alias "tpe" → folder `~/.amelia/trips/tpe/`).

### Step 3: Resolve Preferences

Resolution order (most specific wins):
1. User-provided values in this invocation
2. Trip overrides (from explicit user input)
3. Profile defaults (if profile specified)
4. Global defaults from config.md

Key fields: cabin, stops, auto_widen_days, min_seats, award_search, time windows.
`award_search` defaults to `false` if not set in profile or overrides.

### Step 4: Create Trip Folder

Create folder structure:
```
~/.amelia/trips/{alias}/
├── trip.json
├── flights/
├── hotels/
└── summary.md
```

Write `trip.json`:
```json
{
  "alias": "{alias}",
  "display_name": "{DEST} {Month} Trip",
  "profile": "{profile_name or null}",
  "routes": [
    {"direction": "outbound", "from": "{origin}", "to": "{dest}", "date": "{date}"},
    {"direction": "return", "from": "{dest}", "to": "{origin}", "date": "{return_date}"}
  ],
  "overrides": {
    "cabin": "{cabin}",
    "stops": "{stops}",
    "min_seats": "{min_seats}"
  },
  "award_search": true,
  "hotel_search": {
    "city": "{destination city}",
    "checkin": "{outbound date}",
    "checkout": "{return date}",
    "min_price": 90,
    "max_price": 200,
    "stars": "2,3",
    "brands": "marriott,hyatt,ihg,hilton"
  },
  "created": "{ISO timestamp}",
  "last_searched": "{ISO timestamp}",
  "search_count": 0
}
```

Multi-leg trips: routes can have `"direction": "domestic"` for connecting segments. Example:
```json
"routes": [
  {"direction": "outbound", "from": "SFO", "to": "GRU", "date": "2026-07-17"},
  {"direction": "domestic", "from": "GRU", "to": "JPA", "date": "2026-07-20"},
  {"direction": "domestic", "from": "JPA", "to": "GIG", "date": "2026-07-27"},
  {"direction": "return",   "from": "GRU", "to": "SFO", "date": "2026-07-30"}
]
```

Update `~/.amelia/trip-index.json`:
```json
{"trips": {"...existing...", "{alias}": "{alias}"}}
```

### Step 5: Dispatch Search Subagents

Use the **Agent tool** to dispatch searches in parallel. For each route in `trip.json.routes`:

**IMPORTANT**: Subagents do not have access to `${CLAUDE_PLUGIN_ROOT}`. You must pass the resolved path in every agent prompt. Use this variable in all prompts below:

```
AMELIA_CMD="uv run --directory ${CLAUDE_PLUGIN_ROOT} --env-file ~/.amelia/.env amelia"
```

**Cash flight search (always):**
```
Agent prompt: "You are running the flight-search skill. Read the skill at
${CLAUDE_PLUGIN_ROOT}/skills/flight-search/SKILL.md and follow it exactly. You are in
orchestrated mode — return results as markdown, do NOT write files.

IMPORTANT: The amelia CLI must be run as:
{AMELIA_CMD}
Use this exact command prefix for ALL amelia commands. Do NOT run bare 'amelia'.

Search params:
- Origin: {from}
- Destination: {to}
- Date: {date}
- Cabin: {cabin}
- Stops: {stops}
- Time window: {time_window or 'none'}
- Auto-widen days: {auto_widen_days}"
```

**Award flight search (only if award_search is true):**
```
Agent prompt: "You are running the award-search skill. Read the skill at
${CLAUDE_PLUGIN_ROOT}/skills/award-search/SKILL.md and follow it exactly. You are in
orchestrated mode — return results as markdown, do NOT write files.

IMPORTANT: The amelia CLI must be run as:
{AMELIA_CMD}
Use this exact command prefix for ALL amelia commands. Do NOT run bare 'amelia'.

Search params:
- Origin: {from}
- Destination: {to}
- Date: {date}
- Date range: ±{auto_widen_days} days
- Cabin: {cabin}
- Min seats: {min_seats}"
```

**Hotel search (once per trip, not per route):**
```
Agent prompt: "You are running the hotel-search skill. Read the skill at
${CLAUDE_PLUGIN_ROOT}/skills/hotel-search/SKILL.md and follow it exactly. You are in
orchestrated mode — return results as markdown, do NOT write files.

IMPORTANT: The amelia CLI must be run as:
{AMELIA_CMD}
Use this exact command prefix for ALL amelia commands. Do NOT run bare 'amelia'.

Search params:
- City: {hotel_search.city}
- Check-in: {hotel_search.checkin}
- Check-out: {hotel_search.checkout}
- Min price: {hotel_search.min_price}
- Max price: {hotel_search.max_price}
- Stars: {hotel_search.stars}
- Brands: {hotel_search.brands}"
```

Dispatch all applicable searches simultaneously.

### Step 6: Collect Results and Write Files

Wait for all subagents to return. For each result:

- Cash flights per route → append to `~/.amelia/trips/{alias}/flights/cash-{origin}-{dest}.md`
- Awards per route → append to `~/.amelia/trips/{alias}/flights/awards-{origin}-{dest}.md`
- Hotels → append to `~/.amelia/trips/{alias}/hotels/cash-hotels.md`

Each append is a new run entry:
```markdown
---

## Run: {YYYY-MM-DD HH:MM}

{subagent's returned markdown table}
```

### Step 7: Generate summary.md

Write/overwrite `~/.amelia/trips/{alias}/summary.md`:

```markdown
# Trip: {display_name}

**Route**: {from} → {to} (and any domestic legs)
**Date**: {date} (±{widen} days searched)
**Profile**: {profile}
**Last searched**: {timestamp}
**Total runs**: {count}

---

## Best Cash Flights

{Top 3-5 from cash results table}

## Best Award Flights ({min_seats}+ seats)

{Top 3-5 from award results table, or "Award search not enabled"}

## Hotels

{Top results from hotel search table}

*For points rates, check [rooms.aero](https://rooms.aero)*

---

## Key Findings
- {notable observations}

## Search Params (for re-run)
- Origin: {from}, Dest: {to}, Date: {date}
- Cabin: {cabin}, Stops: {stops}, Min seats: {min_seats}
- Profile: {profile}, Award search: {true/false}
```

### Step 8: Update Metadata

Update `trip.json`: set `last_searched`, increment `search_count`.
Present summary to user.

---

## Mode: Check Again

Triggered by: "/trip check TPE", "TPE trip, check again"

### Step 1: Resolve Alias

1. Read `~/.amelia/trip-index.json`
2. Look up alias (exact match, or search trip.json routes/display_name)
3. No match → ask user to clarify or create new trip

### Step 2: Load Trip State

Read `~/.amelia/trips/{folder}/trip.json` for stored params.
Read last run from flight log files for previous prices.

### Step 3: Re-dispatch Searches

Same as New Trip Step 5, using stored params from trip.json.

### Step 4: Write Results with Change Tracking

Append new results to log files. Compare to previous run:
- **Cash flights**: Match by airline + flight number. Compare price. (`-$XX ↓`, `+$XX ↑`, `same`, `new`)
- **Award flights**: Match by program + airline. Compare miles cost.
- **Hotels**: Match by normalized hotel name. Compare rate_per_night.
- If 3+ runs exist, note overall trend: rising / falling / stable / mixed.

### Step 5: Update summary.md and metadata

Same as New Trip Steps 7-8.

---

## Mode: Recall (Show Cached)

Triggered by: "what did we find for TPE?", "/trip show TPE"

1. Resolve alias
2. Read `~/.amelia/trips/{folder}/summary.md`
3. Present contents to user
4. If user asks for detail, read the full log files

No API calls are made.

---

## Mode: List

Triggered by: "/trip list"

1. Read `~/.amelia/trip-index.json`
2. For each alias, read `trip.json` to get display_name, route, date, last_searched
3. Present as table:

```markdown
| Alias | Route | Date | Profile | Last Searched | Runs |
|-------|-------|------|---------|---------------|------|
| tpe | SFO→TPE | Jul 1 | international-leisure | Mar 23 | 2 |
| brazil | SFO→GRU→JPA→GIG→GRU→SFO | Jul 17 | — | Mar 22 | 2 |
```

---

## Error Handling

- **Subagent fails**: Log the failure in the result file, continue with remaining results.
- **Trip not found**: "No trip found for '{alias}'. Create one with /trip new?"
- **trip-index.json missing or corrupted**: Rebuild by scanning `~/.amelia/trips/*/trip.json`.
- **All searches fail**: Report errors, do not update summary.md.
