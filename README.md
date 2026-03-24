# Amelia

Travel agent CLI + Claude Code plugin for searching flights (cash + award), hotels, and managing trip memory.

## Quick Start

```bash
git clone https://github.com/00derek/amelia
cd amelia
uv sync

# Set API keys
export SEATS_AERO_API_KEY=your-key-here    # Required for award search
export SERPAPI_KEY=your-key-here             # Optional (fast-hotels fallback)

# Use with Claude Code
claude --plugin-dir .
```

Then: `/amelia:trip new SFO TPE 2026-07-01`

## CLI Usage

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
