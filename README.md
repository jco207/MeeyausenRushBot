# MeeyausenRushBot

A Telegram bot that posts one Rush band fact or YouTube video per day to every channel it's added to. Items are picked randomly and won't repeat for at least 30 days.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file:

```
TELEGRAM_BOT_TOKEN=your_token_here
DAILY_POST_TIME=09:00          # optional, default 09:00
DAILY_POST_TZ=America/Los_Angeles  # optional, IANA timezone
```

## Running

```bash
python3 bot.py
```

## Usage

Add the bot to a Telegram channel as an **administrator**. It will automatically register the channel and begin posting daily. Removing the bot from a channel removes it from the rotation.

Send `/test` in a private chat with the bot to immediately push a test post (prefixed with "test") to all registered channels. Test posts are not recorded in history and don't affect the 30-day cooldown.

## Content

Facts and videos live in `Rush-content.md`:

- **Facts** — numbered list items (`1. text`)
- **Videos** — markdown links under `## Videos` (`* [Title](url)`)

Add new entries to either section and they'll be picked up automatically on the next run.
