import time

# 🔥 מיפוי אזורים → זמן הגעה
ZONE_TIME_MAP = {
    "עוטף עזה": 15,
    "מערב הנגב": 15,
    "שער הנגב": 15,
    "אשכול": 15,

    "אשקלון": 30,
    "חוף אשקלון": 30,

    "אשדוד": 45,
    "גן יבנה": 45,
    "יבנה": 45,

    "ראשון לציון": 60,
    "בת ים": 60,
    "חולון": 60,
    "תל אביב": 60,
    "רמת גן": 60,
    "גבעתיים": 60,
    "פתח תקווה": 60,
    "בני ברק": 60,
    "הרצליה": 60,
    "רעננה": 60,
    "כפר סבא": 60,

    "מודיעין": 75,
    "לוד": 70,
    "רמלה": 70,

    "ירושלים": 90,
    "בית שמש": 90,

    "חיפה": 120,
    "קריות": 120,
    "נהריה": 120,
    "עכו": 120,

    "קריית שמונה": 150,
    "צפת": 150,
    "מטולה": 150,
}


# ⏱ זמן הגעה חכם
def estimate_time(areas):
    for area in areas:
        for zone, time_sec in ZONE_TIME_MAP.items():
            if zone in area:
                return time_sec

    return 60  # ברירת מחדל


# 💥 מטח
recent_alerts = []

def detect_barrage():
    global recent_alerts

    now = time.time()
    recent_alerts.append(now)

    recent_alerts = [t for t in recent_alerts if now - t < 10]

    return len(recent_alerts) >= 3


# 🧠 חיזוי מתקדם יותר
def predict_next_area(areas):
    for area in areas:
        if any(x in area for x in ["עוטף", "שדרות", "אשכול"]):
            return "מרכז הארץ בעוד ~60–90 שניות"

        if any(x in area for x in ["אשקלון", "אשדוד"]):
            return "גוש דן בעוד ~45–75 שניות"

        if any(x in area for x in ["חיפה", "קריות"]):
            return "יישובי צפון נוספים בדקות הקרובות"

    return None