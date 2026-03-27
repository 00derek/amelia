---
name: activities
description: Generate ranked things-to-do lists with suggested schedules for a destination. Standalone or dispatched by /trip orchestrator.
---

## Overview

Generates a ranked list of 10-20 things to do for a destination, organized into priority tiers with a loose day-by-day suggested schedule. Uses **web search** for real, validated attraction and restaurant data, then compiles and ranks the results.

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

## Step 1: Web Search (Research Phase)

Run these web searches **in parallel** for the destination city:

1. **Attractions**: `"top things to do in {city} must-see attractions"`
2. **Attractions (TripAdvisor)**: `"{city} best attractions TripAdvisor top rated"`
3. **Restaurants (general)**: `"best restaurants {city} must try food"`
4. **Restaurants (Asian cuisine)**: `"best Asian restaurants {city} Taiwanese Chinese Japanese Korean Thai Vietnamese"`
5. **Breakfast/Brunch**: `"best breakfast brunch {city}"`
6. **Bars & Drinks**: `"best bars cocktails {city}"`

This gives you real, validated data from travel sites, review platforms, and local guides. Do NOT skip the web search step — it prevents hallucinating attractions or restaurants that don't exist.

## Step 2: Compile and Rank (Generation Phase)

Using the web search results, compile **two sections**: Activities (sights/experiences) and Food & Drink (restaurants/bars).

### Activities compilation rules:

1. **Only includes validated items** — every attraction must appear in at least one search result. Do NOT add items from your own knowledge unless they also appear in search results.
2. **Fits the duration** — more items for longer stays, fewer for short stays. 8-15 activities total.
3. **Respects pacing** — 1-2 activities/day max. Arrival and departure days kept light.
4. **Covers variety** — mix of cultural, nature, landmarks, and local experiences.
5. **Prioritizes by impact** — items that appear across multiple sources rank higher. The "Must-do" tier should be the items a traveler would most regret skipping.
6. **Incorporates traveler context** — if interests or profile info provided, weight accordingly.

Activity tier allocation:
- **Must-do**: 3-5 items (the essentials)
- **Highly recommended**: 3-6 items (strong second tier)
- **If you have time**: remainder (good but skippable)

### Food & Drink compilation rules:

1. **Only includes validated items** — every restaurant/bar must appear in at least one search result.
2. **Organize by meal type**, not by ranking tier.
3. **Mix cuisines** — include both Asian and non-Asian options in the lunch/dinner section.
4. **Aim for variety** — don't list 5 of the same cuisine type. Spread across different styles.
5. **3-5 picks per meal category** — enough options without overwhelming.

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

### Food & Drink — {City}

#### Breakfast / Brunch
- **{Name}** — {One-line description}. {Signature dish or order tip}.

#### Lunch / Dinner
**Asian Cuisine**
- **{Name}** — {Cuisine type}. {One-line description}. {Signature dish}.
- ...

**Local & Other Cuisine**
- **{Name}** — {Cuisine type}. {One-line description}. {Signature dish}.
- ...

#### Bars / Drinks
- **{Name}** — {One-line description}. {Vibe or what to order}.

---

### Suggested Schedule (flexible)

| Day | Date | Activities | Food |
|-----|------|------------|------|
| 1 | {checkin} | Arrive, settle in | Evening: {restaurant} |
| 2 | {date} | Morning: {activity} | Lunch: {spot}. Dinner: {spot} |
| ... | ... | ... | ... |
| {N+1} | {checkout} | Morning: free. Depart | Brunch: {spot} |

*1-2 activities/day max. Arrival and departure days kept light.*
```

Format rules:
- Activities: **bold name**, one-line description, rough time commitment (e.g., "Half day", "1-2 hours", "Full day")
- Activities numbered continuously across tiers (1 through N, not restarting per tier)
- Food: **bold name**, cuisine type, one-line description, signature dish or order tip. Bulleted, not numbered.
- Schedule table has separate Activities and Food columns — weaves both together
- Schedule uses morning/afternoon/evening slots, not specific hours
- Arrival and departure days explicitly marked as light

### If Standalone Mode

Present the output directly to the user.

### If Orchestrated Mode

Return the markdown block as text. Do NOT write to any files — the orchestrator handles file writing.

## Error Handling

- **Web search fails**: Fall back to Claude's knowledge with a disclaimer: *"Generated from general knowledge — verify before visiting."*
- **Unknown city**: If the city is too obscure and web search returns thin results, provide what you can with a disclaimer.
- **Very short stay (1 night)**: Generate 3-5 items only, skip the "If you have time" tier, keep schedule to essentials.
- **Very long stay (10+ nights)**: Generate up to 20 items, and note that the schedule leaves plenty of free days for spontaneous exploration.
