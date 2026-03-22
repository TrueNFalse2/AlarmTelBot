import asyncio
import time
from web_server import run_web
import threading
from bot import build_app
from alert_engine import AlertSource, format_alert
from storage import *
from config import BOT_TOKEN
from telegram.ext import ApplicationBuilder
from config import POLL_INTERVAL_SECONDS

source = AlertSource()
cooldown = {}

def match(user_areas, alert_areas):
    return any(
        ua.lower() in aa.lower()
        for ua in user_areas
        for aa in alert_areas
    )

async def send_critical_alert(app, chat_id, text):
    # 🔊 סאונד חזק מאוד
    for _ in range(3):
        await app.bot.send_message(chat_id, "🚨🚨🚨 התרעה!!!")

    await app.bot.send_message(chat_id, text)

    # 🔁 חוזר עד אישור
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

                    # ⏱ cooldown
                    now = time.time()
                    if chat_id in cooldown and now - cooldown[chat_id] < 10:
                        continue

                    text = format_alert(alert)

                    # 🔥 שליחה רגילה + משפחה
                    await send_critical_alert(app, chat_id, text)

                    for member in get_family(chat_id):
                        await send_critical_alert(app, member, text)

                    mark_alert_sent(alert.alert_id, chat_id)
                    cooldown[chat_id] = now

        except Exception as e:
            print("loop error:", e)

        await asyncio.sleep(POLL_INTERVAL_SECONDS)

async def post_init(app):
    # הפעלת הלופ בצורה תקינה לאחר שהאפליקציה עלתה
    app.create_task(alert_loop(app))

def main():
    # 🌍 מפה חיה ברקע
    threading.Thread(target=run_web, daemon=True).start()

    # יצירת האפליקציה עם post_init מובנה
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()

    # טעינת הפקודות מ-bot.py (חשוב לוודא ש-build_app לא יוצר אפליקציה חדשה אלא מוסיף להנדלרים)
    # הערה: אם build_app שלך יוצר אפליקציה חדשה, עדיף לייבא רק את הפונקציה שמוסיפה הנדלרים
    temp_app = build_app()
    app.add_handlers(temp_app.handlers[0]) # הוספת ההנדלרים לאפליקציה המרכזית

    print("🚀 Bot + Map started")
    app.run_polling()

if __name__ == "__main__":
    main()