subscriptions = {}
sent = set()
family_groups = {}
alert_history = []

def add_subscription(chat_id, area):
    subscriptions.setdefault(chat_id, set()).add(area)

def remove_subscription(chat_id, area):
    if chat_id in subscriptions:
        subscriptions[chat_id].discard(area)

def list_subscriptions(chat_id):
    return list(subscriptions.get(chat_id, []))

def get_all_subscriptions():
    return subscriptions

def was_alert_sent(alert_id, chat_id):
    return (alert_id, chat_id) in sent

def mark_alert_sent(alert_id, chat_id):
    sent.add((alert_id, chat_id))

# 👨‍👩‍👧 קבוצות משפחה
def add_family_member(owner, member):
    family_groups.setdefault(owner, set()).add(member)

def get_family(owner):
    return family_groups.get(owner, set())

# 📊 סטטיסטיקה
def log_alert(alert):
    alert_history.append(alert)

def get_stats():
    return len(alert_history)