import logging
import re

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from config import CATEGORIES, TELEGRAM_BOT_TOKEN
from news import fetch_all_news
from subscribers import (
    get_subscriber,
    get_subscribers_for_time,
    has_set_categories,
    mark_categories_prompted,
    set_time,
    subscribe,
    toggle_category,
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
        "/categories — Choose which news categories you want\n"
        "/unsubscribe — Stop receiving digests\n"
        "/status — Check your subscription\n"
        "/now — Get a digest right now"
    )


async def cmd_subscribe(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    subscribe(chat_id, "08:00")
    await update.message.reply_text(
        "Subscribed! You'll receive your digest daily at 08:00.\n"
        "Use /settime to change, e.g. /settime1830\n"
        "Use /categories to pick which sections you want."
    )


async def cmd_unsubscribe(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if unsubscribe(chat_id):
        await update.message.reply_text("Unsubscribed. You won't receive further digests.")
    else:
        await update.message.reply_text("You're not subscribed.")


async def cmd_settime(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id

    raw = update.message.text.split()[0]
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
        enabled = [CATEGORIES[c] for c in sub["categories"] if c in CATEGORIES]
        cats_text = "\n".join(f"  {c}" for c in enabled) if enabled else "  None"
        await update.message.reply_text(
            f"Subscribed — daily digest at {sub['time']}.\n\nCategories:\n{cats_text}"
        )
    else:
        await update.message.reply_text("You're not subscribed. Use /subscribe to start.")


# ── Category selection ────────────────────────────────────────────


def _build_category_keyboard(active_categories: list[str]) -> InlineKeyboardMarkup:
    buttons = []
    for key, label in CATEGORIES.items():
        check = "✅" if key in active_categories else "❌"
        buttons.append([InlineKeyboardButton(f"{check} {label}", callback_data=f"cat:{key}")])
    return InlineKeyboardMarkup(buttons)


async def cmd_categories(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    sub = get_subscriber(chat_id)
    if not sub:
        await update.message.reply_text("You're not subscribed yet. Use /subscribe first.")
        return

    keyboard = _build_category_keyboard(sub["categories"])
    await update.message.reply_text("Tap to toggle categories on/off:", reply_markup=keyboard)


async def handle_category_toggle(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    category = query.data.replace("cat:", "")

    result = toggle_category(chat_id, category)
    if result is None:
        await query.edit_message_text("You're not subscribed. Use /subscribe first.")
        return

    sub = get_subscriber(chat_id)
    keyboard = _build_category_keyboard(sub["categories"])
    await query.edit_message_reply_markup(reply_markup=keyboard)


# ── On-demand digest ──────────────────────────────────────────────


async def cmd_now(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    sub = get_subscriber(chat_id)
    categories = sub["categories"] if sub else list(CATEGORIES.keys())
    await update.message.reply_text("Generating digest, hang tight...")
    await _send_digest_to(update.get_bot(), chat_id, categories)


# ── Digest delivery ───────────────────────────────────────────────


async def _send_message_safe(bot: Bot, chat_id: int, text: str) -> None:
    """Send a message with Markdown, falling back to plain text on parse errors."""
    try:
        await bot.send_message(
            chat_id=chat_id, text=text,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )
    except Exception as e:
        if "parse entities" in str(e).lower() or "can't find end" in str(e).lower():
            logger.warning(f"Markdown parse failed for {chat_id}, sending as plain text")
            await bot.send_message(
                chat_id=chat_id, text=text,
                disable_web_page_preview=True,
            )
        else:
            raise


async def _send_digest_to(bot: Bot, chat_id: int, categories: list[str]) -> None:
    """Build and send digest to a single chat."""
    all_news = fetch_all_news()
    digest = build_digest(all_news, category_keys=categories)

    if len(digest) <= 4096:
        await _send_message_safe(bot, chat_id, digest)
    else:
        for chunk in digest.split("\n\n---\n\n"):
            await _send_message_safe(bot, chat_id, chunk)


async def send_scheduled_digests(time_str: str, bot: Bot) -> None:
    """Send digests to all subscribers whose delivery time matches."""
    subscribers = get_subscribers_for_time(time_str)
    if not subscribers:
        return

    logger.info(f"Sending digest for {time_str} to {len(subscribers)} subscriber(s)")

    all_news = fetch_all_news()

    for chat_id, categories in subscribers:
        try:
            if not has_set_categories(chat_id):
                keyboard = _build_category_keyboard(categories)
                await bot.send_message(
                    chat_id=chat_id,
                    text="You're currently receiving all categories. "
                         "Tap below to customise, or ignore to keep all:",
                    reply_markup=keyboard,
                )
                mark_categories_prompted(chat_id)

            digest = build_digest(all_news, category_keys=categories)
            if len(digest) <= 4096:
                await _send_message_safe(bot, chat_id, digest)
            else:
                for chunk in digest.split("\n\n---\n\n"):
                    await _send_message_safe(bot, chat_id, chunk)
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
    app.add_handler(CommandHandler("categories", cmd_categories))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("now", cmd_now))
    app.add_handler(CallbackQueryHandler(handle_category_toggle, pattern=r"^cat:"))
    return app
