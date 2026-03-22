import asyncio
import time
from web_server import run_web
import threading
from bot import build_app
from alert_engine import AlertSource, format_alert
from storage import *
from config import POLL_INTERVAL_SECONDS
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

source = AlertSource()
cooldown = {}

# מילון זמני הגעה (דוגמאות נפוצות - ניתן להרחיב)
# מילון זמני הגעה מורחב - מבוסס על נתוני פיקוד העורף
ARRIVAL_TIMES = {
    # עוטף עזה ודרום
    "עוטף עזה": "מיידי (0-15 שניות)",
    "שדרות": "15 שניות",
    "נתיבות": "30 שניות",
    "אופקים": "45 שניות",
    "אשקלון": "30 שניות",
    "אשדוד": "45 שניות",
    "באר שבע": "דקה (60 שניות)",
    "אילת": "דקה וחצי (90 שניות)",
    "להבים": "דקה",
    "רהט": "דקה",
    "דימונה": "דקה וחצי (90 שניות)",
    "ערד": "דקה וחצי (90 שניות)",
    "ירוחם": "דקה וחצי (90 שניות)",
    
    # מרכז ושפלה
    "תל אביב - יפו": "דקה וחצי (90 שניות)",
    "רמת גן": "דקה וחצי (90 שניות)",
    "גבעתיים": "דקה וחצי (90 שניות)",
    "בני ברק": "דקה וחצי (90 שניות)",
    "חולון": "דקה וחצי (90 שניות)",
    "בת ים": "דקה וחצי (90 שניות)",
    "ראשון לציון": "דקה וחצי (90 שניות)",
    "פתח תקווה": "דקה וחצי (90 שניות)",
    "ראש העין": "דקה וחצי (90 שניות)",
    "מודיעין": "דקה וחצי (90 שניות)",
    "רחובות": "דקה וחצי (90 שניות)",
    "נס ציונה": "דקה וחצי (90 שניות)",
    "לוד": "דקה וחצי (90 שניות)",
    "רמלה": "דקה וחצי (90 שניות)",
    "יבנה": "דקה",
    
    # שרון וצפון השרון
    "נתניה": "דקה וחצי (90 שניות)",
    "כפר סבא": "דקה וחצי (90 שניות)",
    "רעננה": "דקה וחצי (90 שניות)",
    "הוד השרון": "דקה וחצי (90 שניות)",
    "הרצליה": "דקה וחצי (90 שניות)",
    "חדרה": "דקה וחצי (90 שניות)",
    "עמק חפר": "דקה וחצי (90 שניות)",
    "בת חפר": "דקה וחצי (90 שניות)",
    "קיסריה": "דקה וחצי (90 שניות)",
    
    # צפון וקו העימות
    "קרית שמונה": "מיידי (0-15 שניות)",
    "מטולה": "מיידי (0-15 שניות)",
    "נהריה": "15-30 שניות",
    "עכו": "30 שניות",
    "חיפה": "דקה (60 שניות)",
    "שלומי": "מיידי (0-15 שניות)",
    "מעלות תרשיחא": "30 שניות",
    "חצור הגלילית": "30 שניות",
    "נשר": "דקה",
    "ראש פינה": "30 שניות",
    "יסוד המעלה": "30 שניות",
    "צפת": "30 שניות",
    "כרמיאל": "30 שניות",
    "שומרה": "מיידי (0-15 שניות)",
    "זרעית": "מיידי (0-15 שניות)",
    "ערב אל עראמשה": "מיידי (0-15 שניות)",
    "אביבים": "מיידי (0-15 שניות)",
    "קרית אתא": "דקה (60 שניות)",
    "קרית מוצקין": "דקה (60 שניות)",
    "קרית ביאליק": "דקה (60 שניות)",
    "קרית ים": "דקה (60 שניות)",
    "נשר": "דקה (60 שניות)",
    "טירת כרמל": "דקה (60 שניות)",
    "עכו": "30 שניות",
    "כרמיאל": "30 שניות",
    "צפת": "30 שניות",
    "טבריה": "דקה",
    "עפולה": "דקה",
    "נצרת": "דקה",
    "בית שאן": "דקה",
    "קצרין": "מיידי (15 שניות)",
    "רמת הגולן": "מיידי עד 15 שניות",
    
    # ירושלים ויהודה ושומרון
    "ירושלים": "דקה וחצי (90 שניות)",
    "בית שמש": "דקה וחצי (90 שניות)",
    "מעלה אדומים": "דקה וחצי (90 שניות)",
    "אריאל": "דקה וחצי (90 שניות)",
    "ביתר עילית": "דקה וחצי (90 שניות)",
    "מודיעין עילית": "דקה וחצי (90 שניות)",


    # רמת הגולן (מיידי)
    "קצרין": "מיידי (15 שניות)",
    "מג'דל שמס": "מיידי (15 שניות)",
    "רמת הגולן": "מיידי (15 שניות)",
    "אודם": "מיידי (15 שניות)",
}

async def send_pro_alert(app, chat_id, alert):
    # מציאת זמן הגעה מהמילון
    city = alert.areas[0] if alert.areas else ""
    arrival_time = ARRIVAL_TIMES.get(city, "לפי הנחיות פיקוד העורף")
    
    # קבלת הנחיות לפי הטקסט של ההתראה
    instructions = get_smart_instructions(alert.full_text if hasattr(alert, 'full_text') else str(alert.areas))
    
    text = (
        f"🚨 **התרעה קריטית!**\n\n"
        f"📍 **אזור:** {', '.join(alert.areas)}\n"
        f"⏳ **זמן התגוננות:** {arrival_time}\n\n"
        f"{instructions}"
    )
    
   # יצירת כפתורים מתחת להודעה
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ אני במרחב מוגן - עדכן משפחה", callback_data=f"safe_{chat_id}")],
        [InlineKeyboardButton("🔍 מקלטים קרובים", url="https://www.google.com/maps/search/מקלטים+ציבוריים")]
    ])

    try:
        await app.bot.send_message(chat_id=chat_id, text=text, reply_markup=keyboard, parse_mode='Markdown')
        # הפעלת טיימר סיום אירוע
        asyncio.create_task(end_event_notification(app, chat_id, ", ".join(alert.areas)))
    except Exception as e:
        print(f"Error sending alert: {e}")

def match(user_areas, alert_areas):
    # מנקה רווחים מיותרים והופך לאותיות קטנות להשוואה מדויקת
    clean_user_areas = [ua.strip().lower() for ua in user_areas]
    clean_alert_areas = [aa.strip().lower() for aa in alert_areas]
    
    return any(
        ua in aa or aa in ua
        for ua in clean_user_areas
        for aa in clean_alert_areas
    )

def get_time_for_city(alert_areas):
    # מנקה את השמות של האזורים מהתראה (לפעמים יש שם תווים מיותרים)
    for area in alert_areas:
        clean_area = area.replace("-", " ").strip()
        for city, duration in ARRIVAL_TIMES.items():
            if city in clean_area or clean_area in city:
                return duration
    return "זמן התגוננות - לפי הנחיות פיקוד העורף"

async def end_event_notification(app, chat_id, area_name):
    """שליחת הודעת סיום אירוע לאחר 10 דקות"""
    await asyncio.sleep(600)  # 10 דקות
    try:
        await app.bot.send_message(
            chat_id=chat_id,
            text=f"✅ **חזרה לשגרה: {area_name}**\nחלפו 10 דקות מההתראה האחרונה. ניתן לצאת מהמרחב המוגן."
        )
    except:
        pass

async def send_smart_alert(app, chat_id, alert):
    """שליחת התראה חכמה הכוללת זמן הגעה וכפתור מקלטים"""
    arrival_time = get_time_for_city(alert.areas)
    area_names = ", ".join(alert.areas)
    
    # עיצוב ההודעה
    text = (
        f"🚨 **התרעה בזמן אמת!**\n\n"
        f"📍 **מיקום:** {area_names}\n"
        f"⏳ **זמן כניסה למרחב מוגן:** {arrival_time}\n"
        f"🛡️ שהו במרחב המוגן 10 דקות."
    )
    
    # כפתור למציאת מקלט קרוב
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 מצא מקלט קרוב (Google Maps)", url="https://www.google.com/maps/search/public+shelter")]
    ])

    try:
        # שליחת ההודעה המרכזית (פעם אחת בלבד)
        await app.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        
        # הפעלת טיימר לסיום אירוע ברקע
        asyncio.create_task(end_event_notification(app, chat_id, area_names))
        
    except Exception as e:
        print(f"Error in smart alert to {chat_id}: {e}")

def get_smart_instructions(alert_text):
    """קביעת הנחיות לפי סוג האיום - גרסת PRO"""
    
    # בדיקת חדירת כלי טיס עוין (כטב"ם)
    if "כלי טיס" in alert_text or "כטב" in alert_text:
        return (
            "🛩️ **חדירת כלי טיס עוין (כטב\"ם):**\n"
            "היכנסו למרחב מוגן מיד. האיום עשוי להימשך זמן רב.\n"
            "התרחקו מחלונות ושהו במיגון עד לקבלת הודעה על סיום האירוע."
        )
    
    # בדיקת חדירת מחבלים
    elif "חדירת מחבלים" in alert_text:
        return (
            "⚠️ **חדירת מחבלים:**\n"
            "היכנסו למבנה, נעלו דלתות וחלונות, כבו אורות.\n"
            "התרחקו מהחלונות ואל תצאו עד להודעה מפורשת מכוחות הביטחון."
        )
    
    # בדיקת רעידת אדמה
    elif "רעידת אדמה" in alert_text:
        return (
            "⚠️ **רעידת אדמה:**\n"
            "צאו לשטח פתוח. אם אי אפשר - היכנסו לממ\"ד או לחדר מדרגות.\n"
            "התרחקו ממבנים, עצים ועמודי חשמל."
        )
    
    # בדיקת אירוע חומרים מסוכנים (חומ"ס)
    elif "חומרים מסוכנים" in alert_text:
        return (
            "☣️ **אירוע חומרים מסוכנים:**\n"
            "היכנסו למבנה, סגרו חלונות ודלתות, וכבו מזגנים.\n"
            "אל תשתמשו במאווררים והמתינו להנחיות נוספות."
        )
    
    # ברירת מחדל - ירי רקטות וטילים
    return (
        "🛡️ **ירי רקטות וטילים:**\n"
        "היכנסו למרחב המוגן ושהו בו 10 דקות.\n"
        "זכרו: 'הכי מוגן שיש' - ממ\"ד, חדר מדרגות או חדר פנימי."
    )
def get_smart_instructions(alert_text):
    """קביעת הנחיות לפי סוג האיום - כולל כטב"ם וחומ"ס"""
    alert_text = alert_text.lower()
    if "כלי טיס" in alert_text or "כטב" in alert_text:
        return "🛩️ **חדירת כלי טיס עוין (כטב\"ם):**\nהיכנסו למרחב מוגן מיד. האיום עשוי להימשך זמן רב. שהו במיגון עד להודעה על סיום האירוע."
    elif "חדירת מחבלים" in alert_text:
        return "⚠️ **חדירת מחבלים:**\nהיכנסו למבנה, נעלו דלתות וחלונות, כבו אורות והתרחקו מהחלונות."
    elif "רעידת אדמה" in alert_text:
        return "⚠️ **רעידת אדמה:**\nצאו לשטח פתוח. אם אי אפשר - היכנסו לממ\"ד או לחדר מדרגות."
    elif "חומרים מסוכנים" in alert_text:
        return "☣️ **אירוע חומרים מסוכנים:**\nסגרו חלונות, דלתות ומזגנים. המתינו להנחיות נוספות."
    return "🛡️ **ירי רקטות וטילים:**\nהיכנסו למרחב המוגן ושהו בו 10 דקות."

async def alert_loop(app):
    await asyncio.sleep(2)
    print("📢 Alert Loop Started (Smart Mode)")
    
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

                    # ⏱ cooldown מוגדל למניעת הצפה (30 שניות)
                    now = time.time()
                    if chat_id in cooldown and now - cooldown[chat_id] < 30:
                        continue

                    # שליחה חכמה למשתמש
                    await send_pro_alert(app, chat_id, alert)

                    # שליחה חכמה לבני משפחה
                    for member in get_family(chat_id):
                        await send_smart_alert(app, member, alert)

                    mark_alert_sent(alert.alert_id, chat_id)
                    cooldown[chat_id] = now

        except Exception as e:
            print("loop error:", e)

        await asyncio.sleep(POLL_INTERVAL_SECONDS)

async def on_post_init(application):
    application.create_task(alert_loop(application))

def main():
    # 🌍 שרת ה-Web למפה חיה
    threading.Thread(target=run_web, daemon=True).start()

    # בניית הבוט
    app = build_app()
    app.post_init = on_post_init

    print("🚀 Bot starting with Smart Features...")
    
    # הרצה וניקוי הודעות קודמות
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()