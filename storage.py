import json
import os
import datetime

# בסיס נתונים פשוט בזיכרון (נשמר לקובץ)
subscriptions = {}  # {chat_id: set(["כל הארץ"])}
user_settings = {} # {chat_id: {"lang": "he", "night_mode": False, "lat": None, "lng": None}}
alert_history = []  # רשימה שתשמור את היסטוריית האזעקות האחרונות

def save_data():
    data = {
        "subs": {k: list(v) for k, v in subscriptions.items()},
        "settings": user_settings
    }
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_data():
    global subscriptions, user_settings
    if os.path.exists('data.json'):
        with open('data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            subscriptions = {int(k): set(v) for k, v in data.get("subs", {}).items()}
            user_settings = {int(k): v for k, v in data.get("settings", {}).items()}

# הגדרת רדיוס ברירת מחדל ורדיוס שינה
def get_user_radius(chat_id):
    return get_user_setting(chat_id, "alert_radius", 15) # ברירת מחדל 15 ק"מ

def set_sleep_radius(chat_id, is_sleep_mode):
    radius = 5 if is_sleep_mode else 15
    set_user_setting(chat_id, "alert_radius", radius)


def toggle_user_mode(chat_id, mode_name):
    """משנה את המצב (True/False) ושומר"""
    current = get_user_setting(chat_id, mode_name, False)
    set_user_setting(chat_id, mode_name, not current)
    return not current

def set_user_setting(chat_id, key, value):
    if chat_id not in user_settings:
        user_settings[chat_id] = {"lang": "he", "night_mode": False, "lat": None, "lng": None}
    user_settings[chat_id][key] = value
    save_data()

# שמירת זמן האזעקה האחרונה לכל צ'אט
last_alert_times = {} # {chat_id: datetime}

def update_last_alert_time(chat_id):
    last_alert_times[chat_id] = datetime.datetime.now()
    save_data()

def get_quiet_duration(chat_id):
    last_time = last_alert_times.get(chat_id)
    if not last_time:
        return "לא נרשמו אזעקות לאחרונה"
    
    diff = datetime.datetime.now() - last_time
    hours, remainder = divmod(int(diff.total_seconds()), 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{hours} שעות ו-{minutes} דקות של שקט בגזרתך"

def get_user_setting(chat_id, key, default):
    return user_settings.get(chat_id, {}).get(key, default)

def get_all_users():
    return list(subscriptions.keys())

def get_city_coords(city_name):
    try:
        if os.path.exists('cities.json'):
            with open('cities.json', 'r', encoding='utf-8') as f:
                cities = json.load(f)
                for city in cities:
                    if city['name'].strip() == city_name.strip():
                        return city['lat'], city['lng']
    except: pass
    return None, None

def was_alert_sent(alert_id, chat_id):
    return False # לצורך הבדיקה, בייצור כדאי לנהל לוג שליחות

def mark_alert_sent(alert_id, chat_id):
    pass

load_data()