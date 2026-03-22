from telegram.ext import ApplicationBuilder, CommandHandler
from config import BOT_TOKEN
from storage import *

async def start(update, context):
    await update.message.reply_text(
        "🚨 PRO Alert System\n"
        "/add עיר\n/remove עיר\n/list\n"
        "/family ID\n/status\n/test"
    )

async def add(update, context):
    area = " ".join(context.args)
    add_subscription(update.effective_chat.id, area)
    await update.message.reply_text(f"נוסף: {area}")

async def remove(update, context):
    area = " ".join(context.args)
    remove_subscription(update.effective_chat.id, area)
    await update.message.reply_text(f"הוסר: {area}")

async def list_cmd(update, context):
    areas = list_subscriptions(update.effective_chat.id)
    await update.message.reply_text("\n".join(areas) or "אין אזורים")

async def family(update, context):
    member = int(context.args[0])
    add_family_member(update.effective_chat.id, member)
    await update.message.reply_text("נוסף למשפחה")

async def status(update, context):
    from storage import get_stats
    await update.message.reply_text(f"📊 סה״כ התרעות היום: {get_stats()}")

async def test(update, context):
    await update.message.reply_text("🚨 התרעת בדיקה!")

def build_app():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("remove", remove))
    app.add_handler(CommandHandler("list", list_cmd))
    app.add_handler(CommandHandler("family", family))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("test", test))

    return app