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

Send `/test` in a **private chat with the bot** (not inside a channel) to immediately push a test post to all registered channels. Bots cannot receive messages sent inside a channel, so the command must come from a DM. Test posts are prefixed with `[test]` and are not recorded in history.

To trigger a test post on startup instead, run:

```bash
python3 bot.py --test
```

## Content

Facts and videos live in `Rush-content.md`:

- **Facts** — numbered list items (`1. text`)
- **Videos** — markdown links under `## Videos` (`* [Title](url)`)

Add new entries to either section and they'll be picked up automatically on the next run.
