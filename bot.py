import logging
import re

from telegram import Bot, Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from config import TELEGRAM_BOT_TOKEN
from news import fetch_all_news
from subscribers import (
    get_subscriber,
    get_subscribers_for_time,
    set_time,
    subscribe,
    unsubscribe,
)
from summariser import build_digest

logger = logging.getLogger(__name__)

TIME_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


# ── Command handlers ──────────────────────────────────────────────


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Welcome to the Daily News Digest bot!\n\n"
        "/subscribe — Start receiving daily digests (default 08:00)\n"
        "/settime — Change delivery time, e.g. /settime1830\n"
        "/unsubscribe — Stop receiving digests\n"
        "/status — Check your subscription\n"
        "/now — Get a digest right now"
    )


async def cmd_subscribe(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    subscribe(chat_id, "08:00")
    await update.message.reply_text(
        "Subscribed! You'll receive your digest daily at 08:00.\n"
        "Use /settime to change, e.g. /settime1830"
    )


async def cmd_unsubscribe(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if unsubscribe(chat_id):
        await update.message.reply_text("Unsubscribed. You won't receive further digests.")
    else:
        await update.message.reply_text("You're not subscribed.")


async def cmd_settime(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id

    # Extract digits from the command name itself (e.g. /settime0730 -> "0730")
    raw = update.message.text.split()[0]  # e.g. "/settime0730" or "/settime"
    digits = raw.replace("/settime", "")

    if not digits or len(digits) != 4 or not digits.isdigit():
        await update.message.reply_text("Usage: /settimeHHMM\nExample: /settime0730 or /settime1830")
        return

    hour, minute = int(digits[:2]), int(digits[2:])
    if hour > 23 or minute > 59:
        await update.message.reply_text("Invalid time. Hours 00-23, minutes 00-59.")
        return

    time_str = f"{hour:02d}:{minute:02d}"
    if set_time(chat_id, time_str):
        await update.message.reply_text(f"Delivery time updated to {time_str}.")
    else:
        await update.message.reply_text("You're not subscribed yet. Use /subscribe first.")


async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    sub = get_subscriber(chat_id)
    if sub:
        await update.message.reply_text(f"Subscribed — daily digest at {sub['time']}.")
    else:
        await update.message.reply_text("You're not subscribed. Use /subscribe to start.")


async def cmd_now(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    await update.message.reply_text("Generating digest, hang tight...")
    await _send_digest_to(update.get_bot(), chat_id)


# ── Digest delivery ───────────────────────────────────────────────


async def _send_digest_to(bot: Bot, chat_id: int) -> None:
    """Build and send digest to a single chat."""
    all_news = fetch_all_news()
    digest = build_digest(all_news)

    if len(digest) <= 4096:
        await bot.send_message(chat_id=chat_id, text=digest, parse_mode=ParseMode.MARKDOWN)
    else:
        for chunk in digest.split("\n\n---\n\n"):
            await bot.send_message(chat_id=chat_id, text=chunk, parse_mode=ParseMode.MARKDOWN)


async def send_scheduled_digests(time_str: str, bot: Bot) -> None:
    """Send digests to all subscribers whose delivery time matches."""
    chat_ids = get_subscribers_for_time(time_str)
    if not chat_ids:
        return

    logger.info(f"Sending digest for {time_str} to {len(chat_ids)} subscriber(s)")

    all_news = fetch_all_news()
    digest = build_digest(all_news)

    for chat_id in chat_ids:
        try:
            if len(digest) <= 4096:
                await bot.send_message(chat_id=chat_id, text=digest, parse_mode=ParseMode.MARKDOWN)
            else:
                for chunk in digest.split("\n\n---\n\n"):
                    await bot.send_message(chat_id=chat_id, text=chunk, parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            logger.error(f"Failed to send digest to {chat_id}: {e}")

    logger.info("Scheduled digests sent.")


# ── App builder ───────────────────────────────────────────────────


def build_app() -> Application:
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("subscribe", cmd_subscribe))
    app.add_handler(CommandHandler("unsubscribe", cmd_unsubscribe))
    app.add_handler(MessageHandler(filters.Regex(r"^/settime"), cmd_settime))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("now", cmd_now))
    return app
