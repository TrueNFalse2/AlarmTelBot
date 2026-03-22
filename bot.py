from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from config import BOT_TOKEN
from storage import *

# --- פקודות בסיסיות ---

async def start(update, context):
    await update.message.reply_text(
        "🚨 **מערכת התרעות PRO באוויר**\n\n"
        "פקודות זמינות:\n"
        "➕ `/add עיר` - הוספת עיר למעקב\n"
        "➖ `/remove עיר` - הסרת עיר\n"
        "🧹 `/clear` - מחיקת כל רשימת המעקב\n"
        "📍 `/locate` - הגדרת מיקום אוטומטי\n"
        "📋 `/list` - הצגת רשימת המעקב שלי\n"
        "👨‍👩‍👧 `/family ID` - הוספת בן משפחה לעדכון\n"
        "📊 `/status` - סיכום יומי\n"
        "🔔 `/test` - בדיקת צופר חכמה"
    )

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
    
    # מאזינים למיקום ולכפתורים
    app.add_handler(MessageHandler(filters.LOCATION, handle_location))
    app.add_handler(CallbackQueryHandler(handle_callback))

    return app