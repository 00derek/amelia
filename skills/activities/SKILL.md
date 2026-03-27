---
name: activities
description: Generate ranked things-to-do lists with suggested schedules for a destination. Standalone or dispatched by /trip orchestrator.
---

## Overview

Generates a ranked list of 10-20 things to do for a destination, organized into priority tiers with a loose day-by-day suggested schedule. Uses Claude's knowledge — no external API calls.

Can run standalone (prompts for input) or orchestrated (receives params, returns results).

Each invocation covers **one city/destination**. The trip orchestrator dispatches one per destination stay.

## Read Config

Before generating, read `~/.amelia/config.md` for:
- Any traveler context or interests from profile

## Input Collection (Standalone Mode)

If invoked directly (not by orchestrator), collect missing info using AskUserQuestion. **Ask one question at a time** — don't batch.

1. **City** — ask if not provided (e.g., "Tokyo", "Rio de Janeiro")
2. **Duration** — number of nights, or check-in + check-out dates (e.g., "5 nights", "Jul 21–27")
3. **Interests** — optional, free text (e.g., "food, beaches, history, nightlife")

If orchestrator provides these in the prompt, skip AskUserQuestion and use provided values.

## Generation

Using your knowledge of the destination, generate a ranked list of things to do that:

1. **Fits the duration** — more items for longer stays, fewer for short stays. 10-20 total.
2. **Respects pacing** — 1-2 activities/day max. Arrival and departure days kept light.
3. **Covers variety** — mix of cultural, food, nature, landmarks, and local experiences.
4. **Prioritizes by impact** — the "Must-do" tier should be the items a traveler would most regret skipping.
5. **Incorporates traveler context** — if interests or profile info provided, weight accordingly.

Tier allocation guideline:
- **Must-do**: 3-5 items (the essentials)
- **Highly recommended**: 4-8 items (strong second tier)
- **If you have time**: remainder (good but skippable)

For the suggested schedule:
- Allocate must-do items to the best days (not arrival/departure)
- Keep arrival day to evening-only or rest
- Keep departure day to morning-only or free
- Leave gaps — the schedule should feel relaxed, not packed
- Note any time-sensitive items (e.g., "markets only on weekends", "best at sunset")

## Output Format

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
| {N+1} | {checkout} | Morning: free / last-minute. Depart |

*1-2 activities/day max. Arrival and departure days kept light.*
```

Format rules:
- Each item: **bold name**, one-line description, rough time commitment (e.g., "Half day", "1-2 hours", "Full day")
- Numbered continuously across tiers (1 through N, not restarting per tier)
- Schedule table uses morning/afternoon/evening slots, not specific hours
- Arrival and departure days explicitly marked as light

### If Standalone Mode

Present the output directly to the user.

### If Orchestrated Mode

Return the markdown block as text. Do NOT write to any files — the orchestrator handles file writing.

## Error Handling

- **Unknown city**: If the city is too obscure to generate meaningful recommendations, note this and provide what you can with a disclaimer.
- **Very short stay (1 night)**: Generate 3-5 items only, skip the "If you have time" tier, keep schedule to essentials.
- **Very long stay (10+ nights)**: Generate up to 20 items, and note that the schedule leaves plenty of free days for spontaneous exploration.
