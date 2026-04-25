# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Telegram bot that posts one Rush band fact or YouTube video per day to every channel it's added to. It avoids repeating any item for at least 30 days.

## Running the bot

```bash
# Set up the virtual environment (first time)
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run
python bot.py
```

## Environment variables (`.env`)

| Variable | Required | Default | Description |
|---|---|---|---|
| `TELEGRAM_BOT_TOKEN` | yes | — | Bot token from BotFather |
| `DAILY_POST_TIME` | no | `09:00` | Time to post in `HH:MM` format |
| `DAILY_POST_TZ` | no | `America/Los_Angeles` | IANA timezone for the scheduled post |

## Architecture

Two source files plus a Markdown content database:

- **[bot.py](bot.py)** — Entry point. Builds the `Application`, registers handlers, and schedules the daily job. Key functions:
  - `pick_item()` — Selects a random item, excluding anything posted in the last 30 days. Falls back to the full list if all items are in the cooldown window.
  - `daily_post()` — Loads state, picks an item, broadcasts to all registered channels, then appends to history.
  - `track_membership()` — Listens for `MY_CHAT_MEMBER` events to auto-register/deregister channels when the bot is added or removed.

- **[content.py](content.py)** — Parses `Rush-content.md` into a flat list of dicts. Facts are numbered list items (`1. text`); videos are markdown links under the `## Videos` section (`* [Title](url)`). IDs are `fact_N` and `video_Title_with_underscores`.

- **[Rush-content.md](Rush-content.md)** — The content database: 100 numbered facts across thematic sections, plus ~23 YouTube video links. Add new facts by appending numbered lines; add videos by appending `* [Title](url)` lines under `## Videos`.

- **`state.json`** (runtime, not in git) — Persisted between runs. Structure: `{"channels": [chat_id, ...], "history": [{"item_id": "...", "posted_at": "ISO8601"}, ...]}`.

## Adding content

- **New fact**: Add a numbered line anywhere in the fact sections of `Rush-content.md`. The parser matches `^\d+\.\s+(.+)` per line.
- **New video**: Add a `* [Title](url)` line under `## Videos`. The parser matches `^\*\s+\[(.+?)\]\((.+?)\)`.
- IDs must be unique. Fact IDs are derived from their number; video IDs from their title (spaces → underscores). Avoid duplicate titles.
