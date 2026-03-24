# Amelia

Travel agent CLI + Claude Code plugin for searching flights (cash + award), hotels, and managing trip memory.

## Install as Claude Code Plugin

```
/plugin marketplace add 00derek/amelia
/plugin install amelia@00derek-amelia
```

Python dependencies are installed automatically on first session start via a `SessionStart` hook — no manual setup needed.

If you install during an active session, run `/reload-plugins` to activate.

### API Keys

Create `~/.amelia/.env` with your keys:

```bash
mkdir -p ~/.amelia
cat > ~/.amelia/.env << 'EOF'
SEATS_AERO_API_KEY=your-key-here
SERPAPI_KEY=your-key-here
EOF
```

- `SEATS_AERO_API_KEY` — [Seats.aero Pro](https://seats.aero) key (required for award search)
- `SERPAPI_KEY` — [SerpAPI](https://serpapi.com) key (optional, hotel search fallback)

The plugin loads these automatically — no need to export them in your shell profile.

### Set Up Your Preferences

Run the setup skill to configure your home airport, cabin preferences, loyalty programs, and travel profiles:

```
/amelia:setup
```

It walks you through each section interactively and writes `~/.amelia/config.md`. You can re-run it anytime to update.

## What You Can Ask

### Plan a trip

> "I'm flying from SFO to Taipei around July 1st, business class, 2 passengers. Find me flights and a hotel."

Amelia creates a trip, searches cash flights + award availability + hotels in parallel, and saves everything to `~/.amelia/trips/tpe/` so you can track prices over time.

> "Plan a trip to Brazil — SFO to Sao Paulo July 17, then domestic to Joao Pessoa, then Rio, back from Sao Paulo July 30"

Handles multi-leg itineraries with separate searches per segment.

### Search for flights

> "What's the cheapest nonstop flight from SFO to Tokyo in June?"

> "Find me business class flights to London next Friday, I'm flexible by a few days"

Returns a table with prices, airlines, layover details, and a Google Flights link. Automatically widens the date range if nothing is found on the exact date.

### Find award availability

> "Can I use miles to get to Taipei in July? I need 2 seats in business."

> "What award programs have availability from SFO to Europe this summer?"

Searches Seats.aero across 24 mileage programs. Starts with cached results, then widens dates, then checks bulk availability — uses live search only as a last resort to conserve API quota.

### Search hotels

> "Find me a hotel in Taipei for July 1-5, under $200/night, at least 3 stars"

> "What Marriott or Hyatt options are there in Tokyo for my trip dates?"

Returns rates, ratings, distance, and booking links. Filters by chain, star rating, and budget from your config.

### Track and compare prices

> "Check the Taipei trip again — any price changes?"

> "What did we find for the Brazil trip last time?"

> "Show me all my tracked trips"

Re-runs searches with stored params and shows price changes (↑↓) compared to the last run. Or just recalls cached results without making any API calls.

## CLI Usage (standalone)

If you prefer using the CLI directly without Claude Code:

```bash
git clone https://github.com/00derek/amelia
cd amelia
uv sync
```

```bash
# Cash flights
amelia flights search --from SFO --to TPE --date 2026-07-01

# Award search
amelia awards search --from SFO --to TPE --date 2026-07-01 --end-date 2026-07-07
amelia awards trip <availability-id>
amelia awards availability --source aeroplan --cabin business
amelia awards live --from SFO --to TPE --date 2026-07-01 --source united
amelia awards programs
amelia awards routes --source aeroplan

# Hotels
amelia hotels search --city TPE --checkin 2026-07-01 --checkout 2026-07-05

# Config
amelia config show --profile tournament
```

## Updating

To manually pull the latest version:

```
/plugin update amelia@00derek-amelia
```

Or enable auto-updates so new versions are pulled at startup:

```
/plugin → Marketplaces → 00derek-amelia → Enable auto-update
```

## Configuration

Run `/amelia:setup` to configure interactively, or edit `~/.amelia/config.md` directly. A starter config is created on first run.

You can customize:
- **Global defaults** — home airport, cabin class, stops, hotel budget
- **Loyalty programs** — your memberships and status
- **Profiles** — named presets for different trip types (e.g., "weekend-trip", "international")
- **Active sources** — which hotel chains to search

When you say something like "search using my international profile", Amelia applies that profile's settings on top of your global defaults.

## API Keys

Store keys in `~/.amelia/.env` (loaded automatically by the plugin):

- `SEATS_AERO_API_KEY` — [Seats.aero Pro](https://seats.aero) key for award searches
- `SERPAPI_KEY` — [SerpAPI](https://serpapi.com) key for hotel search (optional)
