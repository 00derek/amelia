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

Set these in your shell profile:

```bash
export SEATS_AERO_API_KEY=your-key-here    # Required for award search
export SERPAPI_KEY=your-key-here             # Optional (fast-hotels fallback)
```

## Skills

### `/amelia:trip` — Trip orchestrator

The main skill. Creates a trip, dispatches flight + award + hotel searches in parallel, and stores results for tracking over time.

```
/amelia:trip new SFO TPE 2026-07-01
```

Amelia will ask for details (cabin, return date, etc.) or pull them from your config profile. It then searches all sources simultaneously and writes results to `~/.amelia/trips/tpe/`.

**Other trip commands:**

| Command | What it does |
|---------|-------------|
| `/amelia:trip check TPE` | Re-run searches with stored params, shows price changes (↑↓) vs last run |
| `/amelia:trip show TPE` | Show cached results without making any API calls |
| `/amelia:trip list` | List all tracked trips with routes, dates, and search counts |

### `/amelia:flight-search` — Cash flights

Searches Google Flights for cash prices on a single route. Can run standalone or dispatched by `/amelia:trip`.

```
/amelia:flight-search
```

Amelia will ask for origin, destination, date, cabin, and stops. Returns a formatted table with prices, layover details, and a Google Flights link. Auto-widens the date range if no results found.

### `/amelia:award-search` — Award flights

Searches Seats.aero for award availability. Requires `SEATS_AERO_API_KEY`.

```
/amelia:award-search
```

Uses a multi-step strategy: cached search first, then widens dates, then bulk availability, then live search as a last resort. Returns miles cost, taxes, routing, and seat count.

### `/amelia:hotel-search` — Hotels

Searches Google Hotels for rates.

```
/amelia:hotel-search
```

Returns hotel name, chain, stars, rate/night, total, rating, and booking links. Filters by price range and star rating from your config.

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

## Configuration

Edit `~/.amelia/config.md` for preferences, profiles, and loyalty programs. Created automatically on first run.

## API Keys

- `SEATS_AERO_API_KEY` — [Seats.aero Pro](https://seats.aero) key for award searches
- `SERPAPI_KEY` — [SerpAPI](https://serpapi.com) key for hotel search (optional)
