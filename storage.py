subscriptions = {}  # {chat_id: set(areas)}
user_locations = {} # {chat_id: (lat, lon)} - חדש!
sent = set()        # {(alert_id, chat_id)}
family_groups = {}  # {owner_id: set(members)}
alert_history = []

# --- ניהול אזורים ---

def add_subscription(chat_id, area):
    if chat_id not in subscriptions:
        subscriptions[chat_id] = set()
    subscriptions[chat_id].add(area)

def remove_subscription(chat_id, area):
    if chat_id in subscriptions:
        subscriptions[chat_id].discard(area)

def clear_all_subscriptions(chat_id):
    """מנקה את כל רשימת המעקב של המשתמש"""
    if chat_id in subscriptions:
        subscriptions[chat_id] = set()
    # אם תרצה למחוק גם את המיקום השמור שלו בזמן הניקוי:
    if chat_id in user_locations:
        del user_locations[chat_id]

def list_subscriptions(chat_id):
    # מחזיר רשימה ממוינת ללא כפילויות
    return sorted(list(subscriptions.get(chat_id, [])))

def get_all_subscriptions():
    return subscriptions

# --- ניהול מיקום GPS (חדש!) ---

def save_user_gps(chat_id, lat, lon):
    """שומר קואורדינטות של משתמש"""
    user_locations[chat_id] = (lat, lon)

def get_user_location(chat_id):
    """שולף מיקום שמור של משתמש"""
    return user_locations.get(chat_id)

# --- מניעת כפילויות בהודעות ---

def was_alert_sent(alert_id, chat_id):
    return (alert_id, chat_id) in sent

def mark_alert_sent(alert_id, chat_id):
    sent.add((alert_id, chat_id))

# --- 👨‍👩‍👧 קבוצות משפחה ---

def add_family_member(owner, member):
    if owner not in family_groups:
        family_groups[owner] = set()
    family_groups[owner].add(member)

def get_family(owner):
    return family_groups.get(owner, set())

# --- 📊 סטטיסטיקה ---

def log_alert(alert):
    alert_history.append(alert)

def get_stats():
    # מחזיר את כמות ההתראות ב-24 השעות האחרונות (לפי ההיסטוריה)
    return len(alert_history)