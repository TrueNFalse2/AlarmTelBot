from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from config import BOT_TOKEN
from storage import *
import asyncio
import matplotlib.pyplot as plt # ספרייה ליצירת גרפים
import io

async def start(update, context):
    chat_id = update.effective_chat.id
    if chat_id not in subscriptions:
        subscriptions[chat_id] = set(["כל הארץ"])
        save_data()
    
    keyboard = [[KeyboardButton("📍 שתף מיקום לסינון התרעות", request_location=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "👋 **ברוכים הבאים ל-Red Alert PRO!**\n\n"
        "🇮🇱 המערכת פועלת במצב ארצי.\n"
        "🌍 ניתן לשנות שפה ב-`/settings`.\n"
        "🤖 לשאלות את ה-AI: `/ai מה עושים עכשיו?`",
        reply_markup=reply_markup, parse_mode='Markdown'
    )

async def stats_cmd(update, context):
    # שליפת נתונים מ-storage (מספר אזעקות ליום)
    days = ["ראשון", "שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת"]
    counts = [12, 45, 23, 89, 34, 10, 5] # דוגמה לנתונים שנמשוך מהלוג שלך
    
    # יצירת הגרף
    plt.figure(figsize=(10, 5))
    plt.bar(days, counts, color='red')
    plt.title("כמות התרעות בשבוע האחרון")
    plt.xlabel("יום בשבוע")
    plt.ylabel("מספר אזעקות")
    
    # שמירת הגרף לקובץ בזיכרון
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    
    await update.message.reply_photo(photo=buf, caption="📊 **סיכום ירי שבועי:**\nנתונים בזמן אמת מהמערכת.")
    plt.close()

async def location_handler(update, context):
    loc = update.message.location
    set_user_setting(update.effective_chat.id, "lat", loc.latitude)
    set_user_setting(update.effective_chat.id, "lng", loc.longitude)
    await update.message.reply_text("📍 המיקום עודכן! תקבל התרעות רק בטווח של 15 ק\"מ ממך.")

async def ai_cmd(update, context):
    from main import get_ai_response
    query = " ".join(context.args)
    if not query: return await update.message.reply_text("שאל אותי משהו אחרי הפקודה.")
    
    msg = await update.message.reply_text("🤖 מעבד נתונים...")
    lang = get_user_setting(update.effective_chat.id, "lang", "he")
    res = await get_ai_response(query, lang)
    await msg.edit_text(res)

async def settings_cmd(update, context):
    keyboard = [
        [InlineKeyboardButton("🇮🇱 עברית", callback_data="lang_he"), InlineKeyboardButton("🇺🇸 English", callback_data="lang_en")],
        [InlineKeyboardButton("🌙 שנה מצב לילה", callback_data="toggle_night")]
    ]
    await update.message.reply_text("⚙️ הגדרות:", reply_markup=InlineKeyboardMarkup(keyboard))

async def radio_cmd(update, context):
    keyboard = [
        [InlineKeyboardButton("📻 גלצ (שידור חי)", url="https://glz.co.il/"),
         InlineKeyboardButton("📻 גלגלצ", url="https://glz.co.il/גלגלצ")],
        [InlineKeyboardButton("📢 כאן רשת ב'", url="https://www.kan.org.il/radio/player.aspx?stationid=3"),
         InlineKeyboardButton("🚨 גל שקט (פיקוד העורף)", url="https://www.ifat.com/GalySheket/")],
        [InlineKeyboardButton("🌐 רדיו דרום", url="http://www.radiodarom.co.il/"),
         InlineKeyboardButton("🌐 רדיו חיפה", url="https://1075.fm/")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🎧 **בחר תחנת רדיו להאזנה ישירה:**\nהשידור יפתח בדפדפן או באפליקציית הרדיו בטלפון שלך.",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def bunker_cmd(update, context):
    chat_id = update.effective_chat.id
    is_active = toggle_user_mode(chat_id, "bunker_mode")
    msg = "🔋 **מצב בונקר הופעל!** מעתה תקבל הודעות טקסט קצרות בלבד לחיסכון בסוללה." if is_active else "🔋 מצב בונקר כובה. חזרה למצב רגיל."
    await update.message.reply_text(msg, parse_mode='Markdown')

async def shabbat_cmd(update, context):
    chat_id = update.effective_chat.id
    is_active = toggle_user_mode(chat_id, "shabbat_mode")
    msg = "🕯️ **מצב שבת הופעל!** תקבל התרעות קוליות בלבד ללא טקסט או מפות." if is_active else "🕯️ מצב שבת כובה."
    await update.message.reply_text(msg, parse_mode='Markdown')


# --- פקודת עזרה ראשונה ---
async def first_aid_cmd(update, context):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🩸 עצירת דימומים", url="https://www.mdais.org/first-aid/bleeding")],
        [InlineKeyboardButton("🧘 טיפול בחרדה (5-4-3-2-1)", callback_data="anxiety_help")],
        [InlineKeyboardButton("🫀 החייאה בסיסית", url="https://www.mdais.org/first-aid/cpr")]
    ])
    await update.message.reply_text(
        "🚑 **מדריך עזרה ראשונה מהיר:**\nבחר את הנושא הרלוונטי לקבלת הנחיות מצילות חיים.",
        reply_markup=keyboard, parse_mode='Markdown'
    )

# --- פקודת מצב שינה (רדיוס 5 ק"מ) ---
async def sleep_mode_cmd(update, context):
    chat_id = update.effective_chat.id
    current_radius = get_user_radius(chat_id)
    new_radius = 5 if current_radius == 15 else 15
    set_user_setting(chat_id, "alert_radius", new_radius)
    
    # וודא שאין נקודות או תווים מוזרים בסוף השורה הזו:
    status = "😴 **מצב שינה פעיל:** רדיוס 5 קילומטר." if new_radius == 5 else "🔔 **מצב רגיל פעיל:** רדיוס 15 קילומטר."
    await update.message.reply_text(status, parse_mode='Markdown')

async def drive_mode(update, context):
    chat_id = update.effective_chat.id
    # שינוי הגדרה ב-storage
    set_user_setting(chat_id, "drive_mode", True)
    await update.message.reply_text("🚗 **מצב נהיגה הופעל!** התראות יושמעו בקול רם אוטומטית.")

async def handle_callback(update, context):
    query = update.callback_query
    await query.answer()
    if query.data.startswith("lang_"):
        set_user_setting(query.message.chat_id, "lang", query.data.split("_")[1])
        await query.message.edit_text("✅ השפה עודכנה!")
# פונקציה לשליחת הודעה לכל המשתמשים (רק למנהל)
async def admin_broadcast(update, context):
    # תחליף את המספר למטה ב-ID האמיתי שלך (אפשר לקבל אותו מבוטים כמו @userinfobot)
    YOUR_ADMIN_ID = 123456789 
    
    if update.effective_user.id != YOUR_ADMIN_ID:
        return # אם זה לא המנהל, הבוט פשוט יתעלם

    if not context.args:
        return await update.message.reply_text("נא לכתוב הודעה לאחר הפקודה. דוגמה: `/broadcast בדיקה`")

    msg = " ".join(context.args)
    users = get_all_users()
    count = 0

    await update.message.reply_text(f"🚀 מתחיל שליחה ל-{len(users)} משתמשים...")

    for user in users:
        try:
            await context.bot.send_message(
                chat_id=user, 
                text=f"📢 **הודעה דחופה מהמערכת:**\n\n{msg}", 
                parse_mode='Markdown'
            )
            count += 1
            # למנוע חסימה מטלגרם בשליחה מאסיבית
            if count % 20 == 0:
                await asyncio.sleep(1) 
        except:
            pass

    await update.message.reply_text(f"✅ השליחה הסתיימה! ההודעה הגיעה ל-{count} משתמשים.")

def build_app():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ai", ai_cmd))
    app.add_handler(CommandHandler("bunker", bunker_cmd))
    app.add_handler(CommandHandler("shabbat", shabbat_cmd))
    app.add_handler(CommandHandler("settings", settings_cmd))
    app.add_handler(MessageHandler(filters.LOCATION, location_handler))
    app.add_handler(CommandHandler("broadcast", admin_broadcast))
    app.add_handler(CallbackQueryHandler(handle_callback))
    return app