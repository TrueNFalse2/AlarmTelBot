import asyncio
import time
from web_server import run_web
import threading
from bot import start, add, remove, list_cmd, family, status, test # Import handlers directly
from alert_engine import AlertSource, format_alert
from storage import *
from config import BOT_TOKEN, POLL_INTERVAL_SECONDS
from telegram.ext import ApplicationBuilder, CommandHandler

source = AlertSource()
cooldown = {}

def match(user_areas, alert_areas):
    return any(
        ua.lower() in aa.lower()
        for ua in user_areas
        for aa in alert_areas
    )

async def send_critical_alert(app, chat_id, text):
    for _ in range(3):
        await app.bot.send_message(chat_id, "🚨🚨🚨 התרעה!!!")
    await app.bot.send_message(chat_id, text)
    for _ in range(2):
        await asyncio.sleep(5)
        await app.bot.send_message(chat_id, "❗ עדיין יש איום! היכנס למרחב מוגן")

async def alert_loop(app):
    while True:
        try:
            alerts = source.fetch_alerts()
            subs = get_all_subscriptions()
            for alert in alerts:
                log_alert(alert)
                for chat_id, areas in subs.items():
                    if not match(areas, alert.areas):
                        continue
                    if was_alert_sent(alert.alert_id, chat_id):
                        continue
                    now = time.time()
                    if chat_id in cooldown and now - cooldown[chat_id] < 10:
                        continue
                    text = format_alert(alert)
                    await send_critical_alert(app, chat_id, text)
                    for member in get_family(chat_id):
                        await send_critical_alert(app, member, text)
                    mark_alert_sent(alert.alert_id, chat_id)
                    cooldown[chat_id] = now
        except Exception as e:
            print("loop error:", e)
        await asyncio.sleep(POLL_INTERVAL_SECONDS)

async def post_init(app):
    # This starts the loop correctly after the bot is ready
    app.create_task(alert_loop(app))

def main():
    # 🌍 Live Heatmap in background
    threading.Thread(target=run_web, daemon=True).start()

    # Create the SINGLE application instance
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()

    # Add handlers from bot.py directly to this instance
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("remove", remove))
    app.add_handler(CommandHandler("list", list_cmd))
    app.add_handler(CommandHandler("family", family))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("test", test))

    print("🚀 Bot + Map started")
    app.run_polling()

if __name__ == "__main__":
    main()