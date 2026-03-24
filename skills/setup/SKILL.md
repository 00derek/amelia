---
name: setup
description: Interactive setup to configure Amelia preferences, loyalty programs, and travel profiles.
---

## Overview

Guides the user through setting up `~/.amelia/config.md` with their travel preferences. Run once after install, or anytime to update preferences.

If `~/.amelia/config.md` already exists, read it first and show the user their current settings before asking what they'd like to change.

## Setup Flow

Walk through each section conversationally. Don't dump all questions at once — ask one section at a time, confirm, then move on.

### Step 1: Basics

Ask the user:

> "Let's set up Amelia. First, the basics — what's your home airport? (e.g., SFO, JFK, LAX)"

Then ask:
- **Travelers** — "How many people do you usually travel with?" (default: 1)
- **Cabin** — "What's your default cabin class?" (economy, premium_economy, business, first — default: economy)
- **Stops** — "Prefer nonstop, or ok with connections?" (0 for nonstop, any — default: any)

### Step 2: Hotels

> "For hotels — what's your typical budget per night?"

- **Min/max price** — e.g., "$100-250" (default: 100-250)
- **Stars** — "Minimum star rating?" (default: 3,4)
- **Chains** — "Any preferred hotel chains?" (default: marriott, hyatt, ihg, hilton)

### Step 3: Loyalty Programs

> "Do you have any airline or hotel loyalty memberships? List them with your status — or skip if you don't want to track these."

Examples to show:
- United: premier silver
- Marriott: gold
- Delta: platinum

If they say none or skip, leave the section with the comment placeholder.

### Step 4: Travel Profiles

> "Profiles are presets for different types of trips — so you don't have to repeat the same preferences every time. Want to set any up?"

Give examples to inspire:
- **weekend-trip** — economy, nonstop, short date flexibility
- **international** — business class, award search enabled, flexible dates, nicer hotels
- **work-travel** — economy, nonstop, specific time windows
- **family-vacation** — 4 travelers, 2+ seats for awards, family-friendly hotels

For each profile they want, ask:
- Profile name
- Which settings differ from their global defaults

They can add as many as they want. When they say they're done, move on.

### Step 5: Award Search

> "Do you have a Seats.aero API key for searching award flights? If so, make sure it's in ~/.amelia/.env. Want award search enabled by default, or just for specific profiles?"

- If they want it globally: set `award_search: true` in global defaults
- If only for certain profiles: set it in those profiles only (default is false)

### Step 6: Write Config

After collecting everything, write `~/.amelia/config.md` in this format:

```markdown
# Amelia Config

## Global Defaults
- home_airport: {airport}
- travelers: {n}
- stops: {stops}
- auto_widen_days: 3
- cabin: {cabin}
- award_search: {true/false}
- hotel_min_price: {min}
- hotel_max_price: {max}
- hotel_stars: {stars}
- hotel_limit: 5

## Loyalty Programs
- {Program}: {status}

## Profiles

### {profile-name}
- {setting}: {value}

## Active Sources
- hotels: [{chains}]
```

### Step 7: Confirm

Show the user the final config and ask if they want to change anything. If yes, make the edits. If not, save and confirm:

> "All set! Your config is at ~/.amelia/config.md — you can edit it anytime. Try `/amelia:trip new {home_airport} {some destination} {a date}` to start searching."

## Updating Existing Config

If `~/.amelia/config.md` already exists:

1. Read and display current settings
2. Ask: "Want to update anything, or add/change a profile?"
3. Only modify the sections they want to change
4. Preserve everything else as-is
