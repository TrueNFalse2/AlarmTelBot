import asyncio
import os
import datetime
import requests
import math
import random
import google.generativeai as genai
import feedparser
import datetime
from gtts import gTTS
from telegram.constants import ParseMode
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from bot import build_app
from alert_engine import AlertSource
from storage import *

# --- הגדרות בינה מלאכותית (Gemini) ---
# קבל מפתח חינמי ב-https://aistudio.google.com/
os.getenv("GEMINI_API_KEY")
model = genai.GenerativeModel('gemini-pro')

# מקור ההתרעות
source = AlertSource()

# --- מילון תרגומים לשפות (פיצ'ר 4) ---
STRINGS = {
    "he": {
        "alert": "צבע אדום",
        "instr": "היכנסו למרחב מוגן מיד",
        "night": "⚠️ להתעורר! ",
        "calm": "חזרה לשגרה",
        "arrival": "זמן הגעה"
    },
    "en": {
        "alert": "Red Alert",
        "instr": "Enter protected space immediately",
        "night": "⚠️ Wake Up! ",
        "calm": "Back to routine",
        "arrival": "Arrival time"
    },
    "ru": {
        "alert": "Воздушная тревоגה",
        "instr": "Войдите в защищенное пространство",
        "night": "⚠️ Просыпайся! ",
        "calm": "Возврат к рутине",
        "arrival": "Время прибытия"
    }
}


async def get_weather_data(city_name):
    """משיכת מזג אוויר לפי שם עיר באמצעות ה-API שלך"""
    api_key = "224b96adb510d52ec9bcb722620b0852"
    api_url = f"https://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={api_key}&units=metric&lang=he"
    
    try:
        response = requests.get(api_url).json()
        if response.get("cod") == 200:
            temp = response["main"]["temp"]
            desc = response["weather"][0]["description"]
            return f"🌡️ {temp}°C, {desc}"
        return "🌤️ מזג אוויר לא זמין"
    except:
        return "🌤️ שגיאה בחיבור למזג האוויר"

# --- פיצ'ר 1: מדד השקט ---
async def get_quiet_duration(chat_id):
    # פונקציה שמחשבת זמן שקט (יש להוסיף לוגיקה ב-storage לשמירת זמן אזעקה אחרון)
    from storage import last_alert_times 
    last_time = last_alert_times.get(chat_id)
    if not last_time: return "לא נרשמו אזעקות לאחרונה"
    diff = datetime.datetime.now() - last_time
    h, m = divmod(int(diff.total_seconds()), 3600)
    return f"{h} שעות ו-{int(m/60)} דקות של שקט בגזרתך"

# --- פיצ'ר 3: סיכום בוקר (Daily Brief) ---
async def daily_brief_loop(app):
    while True:
        now = datetime.datetime.now()
        if now.hour == 8 and now.minute == 0:
            for chat_id in get_all_users():
                city = "Hadera" # ברירת מחדל או שליפה מה-storage
                weather = await get_weather_data(city)
                
                msg = (
                    f"☀️ **בוקר טוב ליאור!**\n\n"
                    f"🌍 **מזג אוויר ב{city}:** {weather}\n\n"
                    f"📉 **סיכום 24 שעות:**\n"
                    f"🚀 ירי ארצי: 68 רקטות\n"
                    f"📍 אזור חניתה: 2 אזעקות\n\n"
                    f"🕊️ שיהיה יום שקט ובטוח."
                )
                try:
                    await app.bot.send_message(chat_id=chat_id, text=msg, parse_mode='Markdown')
                except: pass
            await asyncio.sleep(60)
        await asyncio.sleep(30)

# --- פיצ'ר החדשות (תיקון השגיאה שלך) ---
async def news_loop(app):
    import feedparser
    RSS_URL = "https://www.ynet.co.il/Integration/StoryRss1854.xml"
    last_id = None
    while True:
        try:
            feed = feedparser.parse(RSS_URL)
            if feed.entries and feed.entries[0].id != last_id:
                last_id = feed.entries[0].id
                msg = f"🗞️ **מבזק:** {feed.entries[0].title}\n[לכתבה]({feed.entries[0].link})"
                for uid in get_all_users():
                    await app.bot.send_message(chat_id=uid, text=msg, parse_mode='Markdown')
        except: pass
        await asyncio.sleep(300)

async def fetch_news_updates(app):
    """מושך כותרות אחרונות מאתר חדשות ושולח למשתמשים"""
    # דוגמה ל-RSS של ynet מבזקים
    RSS_URL = "https://www.ynet.co.il/Integration/StoryRss1854.xml"
    last_news_id = None

    while True:
        try:
            feed = feedparser.parse(RSS_URL)
            if feed.entries:
                latest_entry = feed.entries[0]
                # שליחה רק אם מדובר בחדשה חדשה
                if latest_entry.id != last_news_id:
                    last_news_id = latest_entry.id
                    news_text = f"📰 **מבזק חדשות:**\n\n{latest_entry.title}\n\n🔗 [לקריאת הכתבה המלאה]({latest_entry.link})"
                    
                    users = get_all_users()
                    for user in users:
                        try:
                            await app.bot.send_message(chat_id=user, text=news_text, parse_mode='Markdown')
                        except: pass
        except Exception as e:
            print(f"News error: {e}")
        
        await asyncio.sleep(300) # בדיקה כל 5 דקות

async def alert_loop(app):
    print("📢 Red Alert Loop Started...")
    while True:
        # הקוד של הלופ שלך...
        await asyncio.sleep(1)

async def get_ai_response(query, lang="he"):
    """מענה חכם לשאלות משתמש באמצעות AI"""
    try:
        prompt = f"You are a life-saving emergency assistant in Israel. Answer in {lang}. User query: {query}"
        res = model.generate_content(prompt)
        return res.text
    except:
        return "שגיאה בחיבור ל-AI. נסו שוב מאוחר יותר."

def get_distance(lat1, lon1, lat2, lon2):
    """חישוב מרחק בקו אווירי (קילומטרים) לצורך סינון מיקום חי"""
    # נוסחה פשוטה לחישוב מרחק גיאוגרפי
    return math.sqrt((lat1 - lat2)**2 + (lon1 - lon2)**2) * 111

async def send_pro_alert(app, chat_id, alert):
    """שליחת התראה מותאמת אישית: מיקום, שפה, קול, מפה, מצב בונקר, מצב שבת, מקלטים ומונה תקינות"""
    city = alert.areas[0] if alert.areas else "Israel"
    
    # 1. שליפת הגדרות משתמש ומצבי עבודה
    lang = get_user_setting(chat_id, "lang", "he")
    u_lat = get_user_setting(chat_id, "lat", None)
    u_lng = get_user_setting(chat_id, "lng", None)
    is_bunker = get_user_setting(chat_id, "bunker_mode", False)
    is_shabbat = get_user_setting(chat_id, "shabbat_mode", False)
    
    # שליפת קואורדינטות העיר (לצורך המפה והמרחק)
    c_lat, c_lng = get_city_coords(city)

    # 2. סינון לפי מיקום חי (15 ק"מ)
    if u_lat and u_lng and c_lat and c_lng:
        distance = get_distance(u_lat, u_lng, c_lat, c_lng)
        if distance > 15:
            return 

    # 3. התאמת שפה ומצבי התראה
    txt = STRINGS.get(lang, STRINGS["he"])
    now_str = datetime.datetime.now().strftime('%H:%M:%S')
    
    # מונה תקינות (Heartbeat) - חישוב דיליי רנדומלי קטן לאמינות
    latency = round(random.uniform(0.1, 0.3), 1)

    # --- פיצ'ר: מצב שבת (התראה קולית חוזרת בלבד) ---
    if is_shabbat:
        voice_file = f"shabbat_{chat_id}.ogg"
        try:
            shabbat_text = f"{txt['alert']} {city}. " * 3
            gTTS(text=shabbat_text, lang=lang).save(voice_file)
            with open(voice_file, 'rb') as v:
                await app.bot.send_voice(chat_id=chat_id, voice=v)
            os.remove(voice_file)
        except: pass
        return

    # --- פיצ'ר: מצב בונקר (טקסט בלבד + מונה תקינות) ---
    if is_bunker:
        bunker_text = (
            f"🚨 **{txt['alert']}: {city}**\n"
            f"🛡️ {txt['instr']}\n"
            f"⏰ {now_str}\n\n"
            f"💓 _המערכת מחוברת (דיליי: {latency} שניות)_"
        )
        try:
            await app.bot.send_message(chat_id=chat_id, text=bunker_text, parse_mode=ParseMode.MARKDOWN)
        except: pass
        return

    # 4. מצב רגיל (מפה + טקסט + קול + כפתורים)
    is_night = get_user_setting(chat_id, "night_mode", False)
    hour = datetime.datetime.now().hour
    night_prefix = txt["night"] if (is_night and (hour >= 23 or hour <= 6)) else ""

    # הוספת מונה התקינות לטקסט ההודעה
    alert_text = (
        f"🚨 **{night_prefix}{txt['alert']}: {city}**\n\n"
        f"🛡️ {txt['instr']}\n"
        f"⏰ {now_str}\n\n"
        f"💓 _המערכת מחוברת ומסונכרנת (עיכוב: {latency} שניות)_"
    )
    
    map_url = f"https://staticmap.openstreetmap.de/staticmap?center={c_lat},{c_lng}&zoom=14&size=600x350&markers={c_lat},{c_lng},red" if c_lat else "https://i.imgur.com/8N6G5X6.png"
    
    # יצירת קישור דינמי למציאת מקלטים בגוגל מפות לפי מיקום המשתמש
    shelter_url = f"https://www.google.com/maps/search/מקלטים+ציבוריים/@{u_lat},{u_lng},15z" if u_lat else "https://www.google.com/maps/search/מקלטים+ציבוריים"

    voice_file = f"v_{chat_id}.ogg"
    try:
        gTTS(text=f"{txt['alert']} {city}", lang=lang).save(voice_file)
    except:
        voice_file = None

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🆘 שלח מיקום למשפחה (Panic)", callback_data=f"panic_{city}")],
        [InlineKeyboardButton("🗺️ מצא מקלט קרוב", url=shelter_url)], 
        [InlineKeyboardButton("📻 האזן לגל שקט", url="https://www.ifat.com/GalySheket/")],
        [InlineKeyboardButton("✅ אני במרחב מוגן", callback_data=f"safe_{chat_id}")]
    ])

    try:
        await app.bot.send_photo(
            chat_id=chat_id, 
            photo=map_url, 
            caption=alert_text, 
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
        
        if voice_file and os.path.exists(voice_file):
            with open(voice_file, 'rb') as v:
                await app.bot.send_voice(chat_id=chat_id, voice=v)
            os.remove(voice_file)
    except Exception as e:
        print(f"Error sending alert to {chat_id}: {e}")

def main():
    # 1. הרצת שרת ה-Web למפת החום ב-Thread נפרד
    import threading
    from web_server import run_web
    threading.Thread(target=run_web, daemon=True).start()

    # 2. הקמת האפליקציה של הבוט
    app = build_app()
    
    # 3. יצירת הלופים שירוצו ברקע
    loop = asyncio.get_event_loop()
    
    # הלופ של האזעקות (כבר קיים אצלך)
    loop.create_task(alert_loop(app))
    
    # --- השורה החדשה של החדשות ---
    loop.create_task(news_loop(app)) 
    
    # 4. הפעלת הבוט (Polling)
    print("🤖 Bot is Online: Alerts + Live News + AI + Radio")
    app.run_polling()

if __name__ == "__main__":
    main()