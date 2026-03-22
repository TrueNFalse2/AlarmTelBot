from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from config import BOT_TOKEN
from storage import add_subscription, remove_subscription, list_subscriptions


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ברוך הבא לבוט התרעות 🚨\n\n"
        "פקודות:\n"
        "/add <אזור>\n"
        "/remove <אזור>\n"
        "/list\n"
        "/status\n"
        "/test"
    )


async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("דוגמה: /add ראשון לציון")
        return

    area = " ".join(context.args).strip()
    chat_id = update.effective_chat.id
    add_subscription(chat_id, area)
    await update.message.reply_text(f"נרשמת לאזור: {area}")


async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("דוגמה: /remove ראשון לציון")
        return

    area = " ".join(context.args).strip()
    chat_id = update.effective_chat.id
    remove_subscription(chat_id, area)
    await update.message.reply_text(f"הוסר אזור: {area}")


async def list_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    areas = list_subscriptions(chat_id)

    if not areas:
        await update.message.reply_text("אין לך אזורים רשומים.")
        return

    await update.message.reply_text("האזורי התרעה שלך:\n- " + "\n- ".join(areas))


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("הבוט פעיל ומאזין למקורות התרעה.")


async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚨 בדיקת מערכת\n"
        "📍 אזורים: ראשון לציון\n"
        "⏱ זמן הגעה משוער: 60 שניות\n"
        "💥 זוהה רצף התרעות / מטח\n"
        "⚠️ חיזוי: ייתכן המשך למרכז בתוך כ-45–90 שניות\n"
        "🛰 מקור: test\n"
        "📝 זו הודעת בדיקה"
    )


def build_app():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("remove", remove))
    app.add_handler(CommandHandler("list", list_cmd))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("test", test))

    return app