# Activities / Things to Do — Design Spec

## Goal

Add a "things to do" feature to the trip skill. For each destination stay in a multi-leg trip, generate a ranked list of 10-20 activities with a loose suggested day-by-day schedule.

## Requirements

- **Source**: Claude-generated (no external API). Leverage LLM knowledge of destinations.
- **Scope per destination**: 10-20 activities, sorted into 3 tiers:
  - **Must-do** — the non-negotiable highlights
  - **Highly recommended** — strong contenders worth prioritizing
  - **If you have time** — good options for filling gaps
- **Pacing**: 1-2 activities/day max. Arrival and departure days kept light.
- **Schedule**: A loose suggested day-by-day plan (not hour-by-hour). Morning/afternoon/evening slots at most.
- **Flexibility**: The ranked list is the primary output; the schedule is a suggestion, not a rigid itinerary.

## Architecture

### Approach: Standalone Subskill

A new `skills/activities/SKILL.md` subskill, following the same pattern as `flight-search` and `hotel-search`. Dispatched by the trip orchestrator but also usable standalone.

No Python data model, no CLI command, no external API. Pure LLM generation in the skill layer.

### Activities Subskill (`skills/activities/SKILL.md`)

#### Modes

**Standalone mode**: User invokes `/activities` directly. Collects city and duration via AskUserQuestion (one question at a time). Generates and presents results directly.

**Orchestrated mode**: Receives params from trip skill. Returns markdown. Does NOT write files.

#### Input Params (Orchestrated)

| Param | Source | Example |
|-------|--------|---------|
| `city` | `hotel_search[].city` from trip.json | "Joao Pessoa" |
| `checkin` | `hotel_search[].checkin` | "2026-07-21" |
| `checkout` | `hotel_search[].checkout` | "2026-07-27" |
| `traveler_context` | Optional, from profile or user input | "couple, interested in food and beaches" |

#### Input Collection (Standalone)

Ask one question at a time via AskUserQuestion:

1. **City** — required
2. **Duration** — number of days/nights, or checkin + checkout dates
3. **Interests** — optional, free text (e.g., "food, beaches, history")

#### Output Format

```markdown
### Things to Do — {City} ({N} nights, {checkin}–{checkout})

#### Must-Do
1. **{Name}** — {One-line description}. {Time commitment}.
2. ...

#### Highly Recommended
{N+1}. **{Name}** — {One-line description}. {Time commitment}.
...

#### If You Have Time
{M+1}. **{Name}** — {One-line description}. {Time commitment}.
...

---

#### Suggested Schedule (flexible)

| Day | Date | Suggestion |
|-----|------|------------|
| 1 | {checkin} | Arrive, settle in. Evening: {light activity} |
| 2 | {date} | Morning: {activity}. Afternoon: free |
| ... | ... | ... |
| {N} | {checkout} | Morning: free / last-minute. Depart |

*1-2 activities/day max. Arrival and departure days kept light.*
```

Format rules:
- Each item: **bold name**, one-line description, rough time commitment (e.g., "Half day", "1-2 hours", "Full day")
- Numbered continuously across tiers (1-20, not restarting per tier)
- Schedule table uses morning/afternoon/evening slots, not specific hours
- Arrival and departure days explicitly marked as light

### Trip Skill Integration

#### Dispatch

Activities subagents are dispatched **in parallel with** flight/award/hotel searches in Step 5. One agent per destination stay, derived from `hotel_search` entries in `trip.json`.

Agent prompt template:
```
You are running the activities skill. Read the skill at
${CLAUDE_PLUGIN_ROOT}/skills/activities/SKILL.md and follow it exactly.
You are in orchestrated mode — return results as markdown, do NOT write files.

Params:
- City: {hotel_search[i].city}
- Check-in: {hotel_search[i].checkin}
- Check-out: {hotel_search[i].checkout}
- Traveler context: {context from profile/user, or omit}
```

For multi-city trips (e.g., Brazil with 3 destinations), this dispatches 3 activities agents in parallel.

#### File Storage

Results written to:
```
~/.amelia/trips/{alias}/activities/{city-slug}.md
```

Where `city-slug` is the lowercased, hyphenated city name (e.g., `joao-pessoa.md`, `rio-de-janeiro.md`, `sao-paulo.md`).

#### Summary Integration

A new `## Things to Do` section in `summary.md`, placed after the Hotels section. Contains a condensed version per city:
- Must-do tier only (the full ranked list lives in the per-city file)
- Schedule table

#### Check-Again Behavior

Activities are **NOT** re-generated on "check again" runs. They are static knowledge, not live data. Only regenerated if:
- The user explicitly asks to refresh activities
- Trip dates change (which would change the duration and schedule)

#### Folder Structure Update

```
~/.amelia/trips/{alias}/
├── trip.json
├── flights/
├── hotels/
├── activities/          ← NEW
│   ├── sao-paulo.md
│   ├── joao-pessoa.md
│   └── rio-de-janeiro.md
├── price-signals.md
└── summary.md
```

## Changes Required

1. **New file**: `skills/activities/SKILL.md` — the activities subskill
2. **Edit**: `skills/trip/SKILL.md` — add activities dispatch to Step 5, file writing to Step 6, summary section to Step 8, skip on check-again

## Out of Scope

- Python data model for activities (no `models.py` changes)
- CLI command for activities (no `cli.py` changes)
- External API integration (no SerpAPI/Google Places calls)
- Booking links or pricing for activities
- User ratings or reviews
- Map/location data
