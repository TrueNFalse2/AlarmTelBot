import requests
import time
from dataclasses import dataclass
from typing import List

from predictor import detect_barrage, predict_next_area


@dataclass
class Alert:
    alert_id: str
    threat: str
    areas: List[str]
    message: str


class AlertSource:
    def __init__(self):
        self.last_ids = set()

    def fetch_alerts(self):
        try:
            res = requests.get("https://api.tzevaadom.co.il/notifications", timeout=3)

            if res.status_code != 200:
                return []

            data = res.json()

            alerts = []

            for item in data:
                alert_id = str(item.get("id", time.time()))

                if alert_id in self.last_ids:
                    continue

                self.last_ids.add(alert_id)

                alerts.append(
                    Alert(
                        alert_id=alert_id,
                        threat=item.get("title", "🚨 התרעה"),
                        areas=item.get("cities", []),
                        message="היכנס למרחב מוגן"
                    )
                )

            return alerts

        except Exception as e:
            print("fetch error:", e)
            return []


from predictor import detect_barrage, predict_next_area, analyze_all_israel

def format_alert(alert):
    text = f"🚨 {alert.threat}\n"
    text += f"📍 {', '.join(alert.areas)}\n"
    text += "🛑 היכנס למרחב מוגן!\n"

    # 🔮 חיזוי
    pred = predict_next_area(alert.areas)
    if pred:
        text += pred + "\n"

    # 💥 מטח
    if detect_barrage():
        text += "💥 מטח כבד!\n"

    # 📊 מצב ארצי
    analysis = analyze_all_israel(alert.areas)
    if analysis:
        text += analysis

    return text