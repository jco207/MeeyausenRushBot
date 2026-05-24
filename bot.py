import datetime
import json
import logging
import os
import random
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, ChatMemberHandler, CommandHandler, ContextTypes

from content import load_items

load_dotenv()

LOG_FILE = Path(__file__).parent / "log.txt"
STATE_FILE = Path(__file__).parent / "state.json"

_log_fmt = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
_file_handler = logging.FileHandler(LOG_FILE)
_file_handler.setFormatter(_log_fmt)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler(), _file_handler],
)
logger = logging.getLogger(__name__)


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"channels": [], "history": []}


def save_state(state: dict) -> None:
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2))
    tmp.replace(STATE_FILE)


def pick_item(items: list[dict], state: dict) -> dict:
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30)
    recently_posted = {
        h["item_id"] for h in state["history"]
        if datetime.datetime.fromisoformat(h["posted_at"]) > cutoff
    }
    available = [item for item in items if item["id"] not in recently_posted]
    if not available:
        available = items
    return random.choice(available)


def format_message(item: dict) -> str:
    if item["type"] == "fact":
        return f"<b>Rush Fact #{item['number']}</b>\n\n{item['text']}"
    return f'🎵 <a href="{item["url"]}">{item["title"]}</a>'


async def daily_post(context: ContextTypes.DEFAULT_TYPE) -> None:
    state = load_state()
    if not state["channels"]:
        logger.info("No channels registered; skipping daily post.")
        return

    item = pick_item(load_items(), state)
    text = format_message(item)
    posted_to = []

    for channel_id in state["channels"]:
        try:
            await context.bot.send_message(chat_id=channel_id, text=text, parse_mode="HTML")
            posted_to.append(channel_id)
        except Exception as e:
            logger.error("Failed to send to %s: %s", channel_id, e)

    if posted_to:
        state["history"].append({
            "item_id": item["id"],
            "posted_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        })
        save_state(state)
        logger.info("Posted '%s' to %d channel(s): %s", item["id"], len(posted_to), text)


async def track_membership(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    member = update.my_chat_member
    if not member:
        return

    chat_id = member.chat.id
    status = member.new_chat_member.status
    state = load_state()

    if status in ("member", "administrator"):
        if chat_id not in state["channels"]:
            state["channels"].append(chat_id)
            logger.info("Added to chat %s (%s).", member.chat.title, chat_id)
            save_state(state)
    elif status in ("left", "kicked"):
        state["channels"] = [c for c in state["channels"] if c != chat_id]
        logger.info("Removed from chat %s (%s).", member.chat.title, chat_id)
        save_state(state)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Hi! I'm MeeyausenRushBot.\n\nAdd me to a channel as an administrator and I'll post one Rush fact or video per day."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "/start - Introduction\n"
        "/help - Show this message\n"
        "/test - Send a test post (fact or video) to all channels now\n"
        "/test_video - Send a test video link to all channels now"
    )


async def broadcast_test(bot) -> tuple[int, int]:
    state = load_state()
    if not state["channels"]:
        logger.info("No channels registered; skipping test post.")
        return 0, 0

    item = pick_item(load_items(), state)
    text = f"<i>[test]</i> {format_message(item)}"
    sent, failed = 0, 0

    for channel_id in state["channels"]:
        try:
            await bot.send_message(chat_id=channel_id, text=text, parse_mode="HTML")
            sent += 1
        except Exception as e:
            logger.error("Test send failed for %s: %s", channel_id, e)
            failed += 1

    logger.info("Test post sent to %d channel(s): %s", sent, text)
    return sent, failed


def _is_youtube(url: str) -> bool:
    return "youtube.com" in url or "youtu.be" in url


def pick_video(items: list[dict], state: dict) -> dict:
    videos = [item for item in items if item["type"] == "video" and _is_youtube(item["url"])]
    if not videos:
        raise ValueError("No YouTube video items found in content.")
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30)
    recently_posted = {
        h["item_id"] for h in state["history"]
        if datetime.datetime.fromisoformat(h["posted_at"]) > cutoff
    }
    available = [v for v in videos if v["id"] not in recently_posted]
    if not available:
        available = videos
    return random.choice(available)


async def broadcast_test_video(bot) -> tuple[int, int]:
    state = load_state()
    if not state["channels"]:
        logger.info("No channels registered; skipping test-video post.")
        return 0, 0

    item = pick_video(load_items(), state)
    text = f"<i>[test-video]</i> {format_message(item)}"
    sent, failed = 0, 0

    for channel_id in state["channels"]:
        try:
            await bot.send_message(chat_id=channel_id, text=text, parse_mode="HTML")
            sent += 1
        except Exception as e:
            logger.error("Test-video send failed for %s: %s", channel_id, e)
            failed += 1

    logger.info("Test-video post sent to %d channel(s): %s", sent, text)
    return sent, failed


async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    sent, failed = await broadcast_test(context.bot)
    if sent == 0 and failed == 0:
        await update.message.reply_text("No channels registered.")
    else:
        await update.message.reply_text(f"Test post sent to {sent} channel(s){f', {failed} failed' if failed else ''}.")


async def test_video_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    sent, failed = await broadcast_test_video(context.bot)
    if sent == 0 and failed == 0:
        await update.message.reply_text("No channels registered.")
    else:
        await update.message.reply_text(f"Test video sent to {sent} channel(s){f', {failed} failed' if failed else ''}.")


async def startup_test(context: ContextTypes.DEFAULT_TYPE) -> None:
    await broadcast_test(context.bot)


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN not set in .env")

    post_time_str = os.getenv("DAILY_POST_TIME", "09:00")
    post_tz = ZoneInfo(os.getenv("DAILY_POST_TZ", "America/Los_Angeles"))
    try:
        hour, minute = map(int, post_time_str.split(":"))
    except ValueError:
        raise ValueError(f"DAILY_POST_TIME must be in HH:MM format, got: {post_time_str!r}")

    app = Application.builder().token(token).build()

    app.add_handler(ChatMemberHandler(track_membership, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("test", test_command))
    app.add_handler(CommandHandler("test_video", test_video_command))

    app.job_queue.run_daily(
        daily_post,
        time=datetime.time(hour=hour, minute=minute, tzinfo=post_tz),
    )

    if "--test" in sys.argv:
        app.job_queue.run_once(startup_test, when=1)
        logger.info("--test flag detected; sending test post on startup.")

    logger.info("Bot started. Daily post scheduled at %s %s.", post_time_str, post_tz)
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
