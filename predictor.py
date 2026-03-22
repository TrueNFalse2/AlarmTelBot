import time

# 🔥 מפת אזורים מלאה
ISRAEL_REGIONS = {
    "עוטף עזה": ["עוטף", "שדרות", "אשכול", "חוף אשקלון", "נתיב העשרה"],
    "דרום ונגב": ["לכיש", "אשקלון", "אשדוד", "באר שבע", "נגב", "ערבה"],
    "ירושלים ויהודה": ["ירושלים", "מעלה אדומים", "בית שמש", "יהודה", "שומרון"],
    "גוש דן והמרכז": ["דן", "חולון", "ראשון לציון", "תל אביב", "פתח תקווה", "בת ים"],
    "השרון וקו התפר": ["שרון", "עמק חפר", "בת חפר", "נתניה", "הרצליה", "רעננה", "כפר סבא"],
    "צפון - קו העימות": ["גליל עליון", "קו העימות", "קצרין", "גולן", "נהריה", "קרית שמונה"],
    "צפון - חיפה והעמקים": ["חיפה", "קריות", "עמקים", "גליל תחתון", "טבריה", "כרמיאל"]
}

# 🔥 זיהוי מטח
recent_alerts = []

def detect_barrage():
    global recent_alerts
    now = time.time()
    recent_alerts.append(now)
    recent_alerts = [t for t in recent_alerts if now - t < 10]
    return len(recent_alerts) >= 4


# 🔮 חיזוי לפי אזור
def predict_next_area(areas):
    score = 0

    for area in areas:
        if "עוטף" in area:
            score += 3
        if "אשקלון" in area or "אשדוד" in area:
            score += 2
        if "צפון" in area:
            score += 1

    if score >= 4:
        return "🚨 סבירות גבוהה לפגיעה במרכז תוך פחות מדקה"
    elif score >= 2:
        return "⚠️ התפשטות אפשרית למרכז"
    
    return None


# 🧠 ניתוח ארצי מלא
def analyze_all_israel(current_alerts):
    if not current_alerts:
        return None

    detected_districts = {}

    for district, keywords in ISRAEL_REGIONS.items():
        matches = [
            city for city in current_alerts
            if any(key in city for key in keywords)
        ]
        if matches:
            detected_districts[district] = matches

    total_alerts = len(current_alerts)

    report = "\n📊 מצב ארצי:\n"
    report += f"📍 {total_alerts} אזורים פעילים\n"
    report += "------------------\n"

    for dist, cities in detected_districts.items():
        preview = ", ".join(cities[:3])
        if len(cities) > 3:
            preview += "..."
        report += f"{dist}: {len(cities)} ({preview})\n"

    # 🔥 לוגיקה חכמה
    prediction = "\n🔮 ניתוח:\n"

    if total_alerts >= 8:
        prediction += "💥 מטח ארצי רחב!\n"

    if "עוטף עזה" in detected_districts and "דרום ונגב" in detected_districts:
        prediction += "⬅️ התפשטות צפונה מהעוטף\n"

    if "צפון - קו העימות" in detected_districts and len(detected_districts["צפון - קו העימות"]) > 2:
        prediction += "⬅️ מטח בצפון – חיפה בסיכון\n"

    if "השרון וקו התפר" in detected_districts:
        prediction += "‼️ אזור קו התפר בסיכון\n"

    return report + prediction