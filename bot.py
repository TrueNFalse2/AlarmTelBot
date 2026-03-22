from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from config import BOT_TOKEN
from storage import *
from storage import get_top_alerts
# --- פקודות בסיסיות ---

async def start(update, context):
    chat_id = update.effective_chat.id
    user_name = update.effective_user.first_name

    welcome_text = (
        f"👋 **שלום {user_name}! ברוכים הבאים למערכת Red Alert**\n\n"
        "📢 **שימו לב:** כברירת מחדל, אתם מחוברים כרגע ל-**'מצב ארצי'**.\n"
        "זה אומר שתקבלו התרעות על כל אירוע בכל נקודה בארץ 🇮🇱\n\n"
        "📍 **רוצים לקבל התרעות רק על האזור שלכם?**\n"
        "פשוט רשמו: `/add שם העיר` (לדוגמה: `/add נתניה`)\n\n"
        "🛠 **פקודות נוספות:**\n"
        "📋 `/list` - לראות את רשימת המעקב שלכם\n"
        "🧹 `/clear` - למחוק הכל ולחזור למצב ארצי\n"
        "👨‍👩‍👧 `/family ID` - להוסיף בן משפחה לעדכון\n"
        "📊 `/status` - סיכום התרעות יומי\n"
        "🔔 `/test` - בדיקת צופר חכמה (מומלץ!)\n\n"
        "🛡 **יחד ננצח!**\n\n"
        "--- \n"
        "👨‍💻 פותח על ידי ~ TrueNFalse ~"
    )

    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def add(update, context):
    input_text = " ".join(context.args)
    if not input_text:
        return await update.message.reply_text("נא לציין שם עיר. דוגמה: `/add בת חפר`")
    
    # פיצול חכם למקרה שהדבקת רשימה עם /add או פסיקים
    areas = [a.strip() for a in input_text.replace('/add', ',').split(',') if a.strip()]
    
    for area in areas:
        add_subscription(update.effective_chat.id, area)
    
    await update.message.reply_text(f"✅ נוסף למעקב: {', '.join(areas)}")

async def remove(update, context):
    area = " ".join(context.args)
    if not area:
        return await update.message.reply_text("נא לציין עיר להסרה.")
    remove_subscription(update.effective_chat.id, area)
    await update.message.reply_text(f"🗑️ הוסר מהמעקב: {area}")

async def clear_cmd(update, context):
    """מחיקת כל הערים מהרשימה"""
    chat_id = update.effective_chat.id
    # פונקציה שצריכה להיות ב-storage.py למחיקת כל הערים של משתמש
    clear_all_subscriptions(chat_id) 
    await update.message.reply_text("🧹 כל רשימת המעקב שלך נמחקה.")

async def list_cmd(update, context):
    areas = list_subscriptions(update.effective_chat.id)
    unique_areas = sorted(list(set(areas)))
    
    if not unique_areas:
        return await update.message.reply_text("📋 רשימת המעקב שלך ריקה.")
    
    text = "📋 **הערים שלך במעקב:**\n" + "\n".join([f"• {a}" for a in unique_areas])
    await update.message.reply_text(text, parse_mode='Markdown')

# --- מערכת מיקום (חדש!) ---

async def locate_cmd(update, context):
    """שליחת כפתור לבקשת מיקום"""
    location_button = KeyboardButton(text="📍 שתף מיקום להתראות אוטומטיות", request_location=True)
    keyboard = ReplyKeyboardMarkup([[location_button]], resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(
        "כדי שהבוט יזהה אוטומטית אם אתה באזור סכנה, לחץ על הכפתור למטה:",
        reply_markup=keyboard
    )

async def handle_location(update, context):
    """קבלת המיקום ושמירתו"""
    user_location = update.message.location
    chat_id = update.effective_chat.id
    
    # שמירה ב-Database (וודא שיש לך פונקציה כזו ב-storage.py)
    save_user_gps(chat_id, user_location.latitude, user_location.longitude)
    
    await update.message.reply_text(
        "✅ המיקום נשמר! המערכת תתריע אם תהיה סכנה בנקודה שבה אתה נמצא.",
        reply_markup=ReplyKeyboardRemove()
    )

# --- משפחה וסטטוס ---

async def family(update, context):
    if not context.args:
        return await update.message.reply_text("נא לציין ID. דוגמה: `/family 12345678`")
    try:
        member = int(context.args[0])
        add_family_member(update.effective_chat.id, member)
        await update.message.reply_text(f"👨‍👩‍👧 ה-ID {member} נוסף למשפחה.")
    except:
        await update.message.reply_text("ID לא תקין.")

async def status(update, context):
    from storage import get_stats
    await update.message.reply_text(f"📊 סה״כ התרעות היום: {get_stats()}")

async def test(update, context):
    from main import send_pro_alert
    class MockAlert:
        def __init__(self):
            self.areas = ["בדיקה (בת חפר)"]
            self.full_text = "בדיקת מערכת חכמה - כטב\"ם בשמיים"
    
    await send_pro_alert(context.application, update.effective_chat.id, MockAlert())

# --- טיפול בכפתורים ---

async def handle_callback(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("safe_"):
        from main import handle_safe_callback
        await handle_safe_callback(update, context)

async def night_mode_cmd(update, context):
    chat_id = update.effective_chat.id
    current = get_pref(chat_id, "night_mode")
    set_pref(chat_id, "night_mode", not current)
    status = "מופעל 🌙 (התראות רגילות יושתקו, כטב\"ם/חדירה יצלצלו)" if not current else "כבוי ☀️"
    await update.message.reply_text(f"מצב לילה חכם: {status}")

async def silent_wave_cmd(update, context):
    chat_id = update.effective_chat.id
    current = get_pref(chat_id, "silent_wave")
    set_pref(chat_id, "silent_wave", not current)
    status = "מופעל 🔊 (תקבל הודעה קולית בכל אזעקה)" if not current else "כבוי 🤫"
    await update.message.reply_text(f"גל שקט: {status}")

async def help_me_cmd(update, context):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🧘 התקף חרדה - נשימות", callback_data="help_anxiety")],
        [InlineKeyboardButton("🩸 עזרה ראשונה - פציעה", callback_data="help_injury")],
        [InlineKeyboardButton("📞 טלפונים חיוניים", callback_data="help_phones")]
    ])
    await update.message.reply_text("🆘 **תפריט עזרה מהירה:**\nבחר את סוג העזרה הנדרשת:", reply_markup=keyboard, parse_mode='Markdown')

async def top_alerts_cmd(update, context):

    top_list = get_top_alerts()
    
    if not top_list:
        return await update.message.reply_text("📊 עדיין אין מספיק נתונים לסיכום התרעות.")
    
    text = "📊 **סיכום התרעות - היישובים המותקפים ביותר:**\n\n"
    
    for i, (city, count) in enumerate(top_list, 1):
        # הוספת אימוג'י לפי המיקום בדירוג
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🔹"
        text += f"{medal} **{city}**: {count} התרעות\n"
    
    text += "\n_הנתונים מבוססים על ההיסטוריה שנצברה במערכת_"
    await update.message.reply_text(text, parse_mode='Markdown')

# --- בניית האפליקציה ---

def build_app():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # פקודות
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("remove", remove))
    app.add_handler(CommandHandler("clear", clear_cmd))
    app.add_handler(CommandHandler("list", list_cmd))
    app.add_handler(CommandHandler("family", family))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("test", test))
    app.add_handler(CommandHandler("locate", locate_cmd))
    app.add_handler(CommandHandler("night", night_mode_cmd))
    app.add_handler(CommandHandler("wave", silent_wave_cmd))
    app.add_handler(CommandHandler("help_me", help_me_cmd))
    app.add_handler(MessageHandler(filters.LOCATION, handle_location))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(CommandHandler("top", top_alerts_cmd))

    return app