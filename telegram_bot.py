import os
from dotenv import load_dotenv

load_dotenv()

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ConversationHandler, ContextTypes
import config as cfg
import datetime
from schedule_logic import get_schedule, WeeklySchedule
from calendar_utils import create_weekly_events_in_calendar

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def get_date_str(day_index):
    """
    Receives a day index (0-6) and returns a string with the upcoming date.
    For example: 'Sunday (17/12)'
    """
    today = datetime.date.today()
    # Calculate the date (same logic as in calendar_utils)
    current_weekday = (today.weekday() + 1) % 7  # Adjust to our indices (0=Sunday)
    days_ahead = day_index - current_weekday
    if days_ahead <= 0:
        days_ahead += 7

    target_date = today + datetime.timedelta(days=days_ahead)
    return f"{cfg.HEBREW_DAYS[day_index]} ({target_date.day}/{target_date.month})"

# --- Helper function for keyboard ---
def build_days_keyboard(prefix, selected_indices=None, exclude_indices=None, include_done=True, include_none=False):
    if selected_indices is None: selected_indices = []
    if exclude_indices is None: exclude_indices = []

    buttons = []
    is_date_step = "DATE" in prefix or "DH_" in prefix or "DA_" in prefix
    limit = 7 if is_date_step else 6

    for i in range(limit):
        if i in exclude_indices: continue
        day_name = cfg.HEBREW_DAYS[i]
        is_selected = i in selected_indices
        text = f"✅ {day_name}" if is_selected else day_name
        callback_data = f"{prefix}{i}"
        buttons.append(InlineKeyboardButton(text, callback_data=callback_data))

    rows = [buttons[i:i + 3] for i in range(0, len(buttons), 3)]
    controls = []
    if include_done:
        controls.append(InlineKeyboardButton("✅ המשך לשלב הבא", callback_data=f"{prefix}{cfg.ACTION_DONE}"))
    if include_none:
        controls.append(InlineKeyboardButton("❌ ללא / דלג", callback_data=f"{prefix}{cfg.ACTION_NONE}"))
    if controls:
        rows.append(controls)

    return InlineKeyboardMarkup(rows)


def is_authorized(update: Update):
    """Check if the user is in the authorized users list."""
    # If the list is empty, don't authorize anyone
    if not cfg.AUTHORIZED_USER_IDS:
        return False

    # Check if the current user's ID is in the list
    if update.effective_user.id not in cfg.AUTHORIZED_USER_IDS:
        return False

    return True


async def thursday_push(context: ContextTypes.DEFAULT_TYPE):
    chat_id = cfg.ADMIN_CHAT_ID
    if not chat_id:
        return

    await context.bot.send_message(
        chat_id=chat_id,
        text="חמישי הגיע 🙂 אם תרצי לסדר לו״ז מחדש כתבי /start"
    )


# --- HANDLERS with state memory ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        await update.message.reply_text("⛔️ אין לך הרשאה להשתמש בבוט זה. הבוט משרת משתמשים מורשים בלבד.")
        return ConversationHandler.END

    context.user_data['schedule_obj'] = WeeklySchedule()

    if cfg.KIMEL_COUNTER_KEY not in context.application.bot_data:
        context.application.bot_data[cfg.KIMEL_COUNTER_KEY] = cfg.KIMEL_INITIAL_COUNT

    text = "היי! בואו נסדר את הלו\"ז.\n🗓 **שלב 1: ימי איסוף של הילה (בבוקר)**"
    kb = build_days_keyboard(cfg.PREFIX_PICKUP, [], include_done=True)
    await update.message.reply_text(text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
    return cfg.STATE_PICKUP


async def handle_pickup_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if not is_authorized(update):
        await query.answer("⛔️ You are not authorized to perform this action.", show_alert=True)
        await query.edit_message_text("⛔️ Bot usage is restricted to authorized users only.")
        return ConversationHandler.END

    await query.answer()
    data = query.data
    action = data.replace(cfg.PREFIX_PICKUP, "")
    schedule = get_schedule(context)

    if action == cfg.ACTION_DONE:
        # Calculate remaining days for Alon
        all_days = set(range(6))
        hila_days = set(schedule.hila_pickup_indices)
        alon_days = all_days - hila_days

        hila_txt = ', '.join([get_date_str(i) for i in sorted(hila_days)]) or 'ללא'
        alon_txt = ', '.join([get_date_str(i) for i in sorted(alon_days)]) or 'ללא'

        final_text = (
            f"✅ **סיכום איסוף בוקר (עם תאריכים):**\n"
            f"👩 הילה: {hila_txt}\n"
            f"👨 אלון: {alon_txt}"
        )

        await query.edit_message_text(text=final_text, parse_mode=ParseMode.MARKDOWN)

        # Send new message for next step
        next_text = "**שלב 2: דייט שבועי - הילה 🍷**\nבחר את היום הרצוי:"
        kb = build_days_keyboard(cfg.PREFIX_DATE_HILA, include_done=False)
        await context.bot.send_message(chat_id=query.message.chat_id, text=next_text, reply_markup=kb,
                                       parse_mode=ParseMode.MARKDOWN)

        return cfg.STATE_DATE_HILA

    # Regular toggle logic
    schedule.toggle_pickup(int(action))
    new_kb = build_days_keyboard(cfg.PREFIX_PICKUP, selected_indices=schedule.hila_pickup_indices)
    try:
        await query.edit_message_reply_markup(new_kb)
    except:
        pass
    return cfg.STATE_PICKUP


async def handle_date_hila_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if not is_authorized(update):
        await query.answer("⛔️ You are not authorized to perform this action.", show_alert=True)
        await query.edit_message_text("⛔️ Bot usage is restricted to authorized users only.")
        return ConversationHandler.END

    await query.answer()
    day_index = int(query.data.replace(cfg.PREFIX_DATE_HILA, ""))
    schedule = get_schedule(context)
    schedule.set_date_hila(day_index)

    # Freeze old message
    await query.edit_message_text(f"✅ נבחר דייט להילה: **{cfg.HEBREW_DAYS[day_index]}**", parse_mode=ParseMode.MARKDOWN)

    # New message
    kb = build_days_keyboard(cfg.PREFIX_DATE_ALON, exclude_indices=[day_index], include_done=False)
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="**שלב 3: דייט שבועי - אלון 🍺**\nבחר את היום הרצוי:",
        reply_markup=kb, parse_mode=ParseMode.MARKDOWN
    )
    return cfg.STATE_DATE_ALON


async def handle_date_alon_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if not is_authorized(update):
        await query.answer("⛔️ You are not authorized to perform this action.", show_alert=True)
        await query.edit_message_text("⛔️ Bot usage is restricted to authorized users only.")
        return ConversationHandler.END

    await query.answer()
    day_index = int(query.data.replace(cfg.PREFIX_DATE_ALON, ""))
    schedule = get_schedule(context)
    schedule.set_date_alon(day_index)

    # Freeze message
    await query.edit_message_text(f"✅ נבחר דייט לאלון: **{cfg.HEBREW_DAYS[day_index]}**", parse_mode=ParseMode.MARKDOWN)

    # New message
    kb = build_days_keyboard(cfg.PREFIX_KIMEL, [], include_done=True, include_none=True)
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="**שלב 4: קימל בגן 🧸**\nסמן את הימים:",
        reply_markup=kb, parse_mode=ParseMode.MARKDOWN
    )
    return cfg.STATE_KIMEL


async def handle_kimel_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if not is_authorized(update):
        await query.answer("⛔️ You are not authorized to perform this action.", show_alert=True)
        await query.edit_message_text("⛔️ Bot usage is restricted to authorized users only.")
        return ConversationHandler.END

    await query.answer()
    data = query.data
    action = data.replace(cfg.PREFIX_KIMEL, "")
    schedule = get_schedule(context)

    if action == cfg.ACTION_DONE or action == cfg.ACTION_NONE:
        if action == cfg.ACTION_NONE: schedule.clear_kimel()

        # Freeze current Kimel message
        kimel_txt = ', '.join([cfg.HEBREW_DAYS[i] for i in schedule.kimel_indices]) or "ללא"
        await query.edit_message_text(f"✅ נבחרו ימי קימל: {kimel_txt}", parse_mode=ParseMode.MARKDOWN)

        # New message for final summary
        summary = schedule.get_summary_text()
        buttons = [
            [InlineKeyboardButton("🚀 אשר וצור אירועים", callback_data=cfg.ACTION_CONFIRM)],
            [InlineKeyboardButton("❌ בטל הכל", callback_data=cfg.ACTION_CANCEL)]
        ]
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=summary,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.MARKDOWN
        )
        return cfg.STATE_CONFIRM

    # Toggle days
    day_index = int(action)
    schedule.toggle_kimel(day_index)
    new_kb = build_days_keyboard(cfg.PREFIX_KIMEL, selected_indices=schedule.kimel_indices, include_done=True,
                                 include_none=True)
    try:
        await query.edit_message_reply_markup(new_kb)
    except:
        pass
    return cfg.STATE_KIMEL


async def handle_final_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if not is_authorized(update):
        await query.answer("⛔️ You are not authorized to perform this action.", show_alert=True)
        await query.edit_message_text("⛔️ Bot usage is restricted to authorized users only.")
        return ConversationHandler.END

    await query.answer()

    if query.data == cfg.ACTION_CONFIRM:
        await query.edit_message_text("🚀 יוצר אירועים ביומן... אנא המתן.", parse_mode=ParseMode.MARKDOWN)

        # --- Here's where the magic happens ---
        schedule = get_schedule(context)
        try:
            results_text = create_weekly_events_in_calendar(
                schedule, context.application.bot_data
            )
            await context.bot.send_message(chat_id=query.message.chat_id, text=results_text)
        except Exception as e:
            logger.error(f"Calendar Error: {e}")
            await context.bot.send_message(chat_id=query.message.chat_id, text=f"❌ שגיאה ביצירת אירועים: {e}")

        return ConversationHandler.END
    else:
        await query.edit_message_text("בוטל. ניתן להתחיל מחדש עם /start")
        return ConversationHandler.END


# --- 3. MAIN APP SETUP ---
def main():
    if not cfg.TELEGRAM_BOT_TOKEN:
        print("Error: Token is missing!")
        return

    app = Application.builder().token(cfg.TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            cfg.STATE_PICKUP: [CallbackQueryHandler(handle_pickup_step, pattern=f"^{cfg.PREFIX_PICKUP}")],
            cfg.STATE_DATE_HILA: [CallbackQueryHandler(handle_date_hila_step, pattern=f"^{cfg.PREFIX_DATE_HILA}")],
            cfg.STATE_DATE_ALON: [CallbackQueryHandler(handle_date_alon_step, pattern=f"^{cfg.PREFIX_DATE_ALON}")],
            cfg.STATE_KIMEL: [CallbackQueryHandler(handle_kimel_step, pattern=f"^{cfg.PREFIX_KIMEL}")],

            cfg.STATE_CONFIRM: [CallbackQueryHandler(handle_final_confirmation)]
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)]
    )

    app.add_handler(conv_handler)

    app.job_queue.run_daily(
        thursday_push,
        time=datetime.time(hour=10, minute=0),
        days=(4,)  # 0=Mon ... 3=Thu
    )

    app.job_queue.run_once(
        thursday_push,
        when=60
    )

    print("Bot is running...")
    app.run_polling()


if __name__ == '__main__':
    main()