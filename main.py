import asyncio
import time
from web_server import run_web
import threading
from bot import build_app
from alert_engine import AlertSource, format_alert
from storage import *
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
        try:
            await app.bot.send_message(chat_id, "🚨🚨🚨 התרעה!!!")
        except Exception as e:
            print(f"Error sending message to {chat_id}: {e}")

    try:
        await app.bot.send_message(chat_id, text)
    except Exception as e:
        print(f"Error sending text to {chat_id}: {e}")

    # 🔁 חוזר עד אישור
    for _ in range(2):
        await asyncio.sleep(5)
        try:
            await app.bot.send_message(chat_id, "❗ עדיין יש איום! היכנס למרחב מוגן")
        except:
            pass

async def alert_loop(app):
    # נותנים לבוט שנייה להתאפס לפני שהלופ מתחיל
    await asyncio.sleep(2)
    print("📢 Alert Loop Started")
    
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

# פונקציית האתחול שמתבצעת ברגע שהבוט מתחבר בהצלחה
async def on_post_init(application):
    application.create_task(alert_loop(application))

def main():
    # 🌍 מפה חיה ברקע (שרת ה-Web)
    threading.Thread(target=run_web, daemon=True).start()

    # בניית ה-Application
    app = build_app()
    
    # חיבור פונקציית ה-post_init בצורה נכונה
    app.post_init = on_post_init

    print("🚀 Bot starting...")
    
    # הוספת drop_pending_updates=True פותרת את ה-Conflict
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()