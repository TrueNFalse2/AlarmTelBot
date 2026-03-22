import json
import time
from dataclasses import dataclass
from typing import List, Any

import requests

from predictor import estimate_time, detect_barrage, predict_next_area


@dataclass
class Alert:
    alert_id: str
    threat: str
    areas: List[str]
    message: str
    source: str = "unknown"


class MultiSourceAlert:
    def __init__(self):
        self.last_ids: set[str] = set()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json, text/plain, */*",
        })

    def fetch_alerts(self) -> List[Alert]:
        sources = [
            self.from_tzevaadom,
            self.from_kore,
            self.from_mako,
            self.from_prog,
            self.from_oref_live,
        ]

        collected: List[Alert] = []
        for source in sources:
            try:
                alerts = source()
                if alerts:
                    collected.extend(alerts)
            except Exception as e:
                print(f"source error: {source.__name__}: {e}")

        # הסרת כפילויות לפי alert_id
        unique: List[Alert] = []
        seen = set()
        for alert in collected:
            if alert.alert_id in seen:
                continue
            seen.add(alert.alert_id)
            unique.append(alert)

        return unique

    def _mark_and_filter(self, alert_id: str) -> bool:
        if alert_id in self.last_ids:
            return False
        self.last_ids.add(alert_id)

        # ניקוי בסיסי כדי שה-set לא יתנפח בלי סוף
        if len(self.last_ids) > 5000:
            self.last_ids = set(list(self.last_ids)[-2000:])
        return True

    def from_tzevaadom(self) -> List[Alert]:
        url = "https://api.tzevaadom.co.il/notifications"
        res = self.session.get(url, timeout=3)
        data = res.json()

        if not isinstance(data, list):
            return []

        alerts: List[Alert] = []
        for item in data:
            if not isinstance(item, dict):
                continue

            areas = item.get("cities") or item.get("data") or []
            if not isinstance(areas, list):
                areas = []

            alert_id = str(item.get("id") or item.get("notificationId") or f"tzeva-{time.time_ns()}")
            if not self._mark_and_filter(alert_id):
                continue

            alerts.append(
                Alert(
                    alert_id=alert_id,
                    threat=str(item.get("title") or "התרעה"),
                    areas=[str(x) for x in areas],
                    message=str(item.get("message") or "היכנסו למרחב מוגן"),
                    source="tzevaadom",
                )
            )

        return alerts

    def from_kore(self) -> List[Alert]:
        url = "https://www.kore.co.il/redAlert.json"
        res = self.session.get(url, timeout=3)
        data = res.json()

        if data is None:
            return []

        if isinstance(data, dict):
            data = [data]

        if not isinstance(data, list):
            return []

        alerts: List[Alert] = []
        for item in data:
            if not isinstance(item, dict):
                continue

            areas = item.get("cities") or item.get("data") or item.get("areas") or []
            if isinstance(areas, str):
                areas = [areas]
            if not isinstance(areas, list):
                areas = []

            if not areas:
                continue

            alert_id = str(item.get("id") or f"kore-{','.join(areas)}")
            if not self._mark_and_filter(alert_id):
                continue

            alerts.append(
                Alert(
                    alert_id=alert_id,
                    threat="צבע אדום",
                    areas=[str(x) for x in areas],
                    message="היכנסו למרחב מוגן",
                    source="kore",
                )
            )

        return alerts

    def from_mako(self) -> List[Alert]:
        url = "https://www.mako.co.il/Collab/amudanan/alerts.json"
        res = self.session.get(url, timeout=3)
        data = res.json()

        # לפי בדיקה נוכחית, mako מחזיר אובייקט עם id + data
        if isinstance(data, dict):
            areas = data.get("data") or []
            if not isinstance(areas, list) or not areas:
                return []

            alert_id = str(data.get("id") or f"mako-{time.time_ns()}")
            if not self._mark_and_filter(alert_id):
                return []

            return [
                Alert(
                    alert_id=alert_id,
                    threat="התרעה",
                    areas=[str(x) for x in areas],
                    message="היכנסו למרחב מוגן",
                    source="mako",
                )
            ]

        return []

    def from_prog(self) -> List[Alert]:
        url = "https://www.prog.co.il/pakar-tests.php?a=3"
        res = self.session.get(url, timeout=3)
        data = res.json()

        if not isinstance(data, dict):
            return []

        items = data.get("items") or []
        if not isinstance(items, list):
            return []

        alerts: List[Alert] = []
        for item in items:
            if not isinstance(item, dict):
                continue

            areas = item.get("cities") or item.get("data") or []
            if isinstance(areas, str):
                areas = [areas]
            if not isinstance(areas, list):
                areas = []

            if not areas:
                continue

            alert_id = str(item.get("id") or f"prog-{time.time_ns()}")
            if not self._mark_and_filter(alert_id):
                continue

            alerts.append(
                Alert(
                    alert_id=alert_id,
                    threat=str(item.get("title") or "בדיקה"),
                    areas=[str(x) for x in areas],
                    message=str(item.get("desc") or "בדיקת מערכת"),
                    source="prog",
                )
            )

        return alerts

    def from_oref_live(self) -> List[Alert]:
        # מקור פחות יציב, אז נעטוף בזהירות
        url = f"https://www.oref.org.il/WarningMessages/alert/Alerts.json?rand={int(time.time())}"
        headers = {"Referer": "https://www.oref.org.il/"}
        res = self.session.get(url, headers=headers, timeout=3)

        if not res.text.strip():
            return []

        clean = res.text.encode().decode("utf-8-sig")

        try:
            data: Any = json.loads(clean)
        except json.JSONDecodeError:
            return []

        if isinstance(data, dict):
            areas = data.get("data") or []
            if isinstance(areas, str):
                areas = [areas]
            if not isinstance(areas, list) or not areas:
                return []

            alert_id = str(data.get("id") or f"oref-{time.time_ns()}")
            if not self._mark_and_filter(alert_id):
                return []

            return [
                Alert(
                    alert_id=alert_id,
                    threat=str(data.get("title") or "התרעה"),
                    areas=[str(x) for x in areas],
                    message=str(data.get("desc") or "היכנסו למרחב מוגן"),
                    source="oref",
                )
            ]

        if isinstance(data, list):
            alerts: List[Alert] = []
            for item in data:
                if not isinstance(item, dict):
                    continue

                areas = item.get("data") or []
                if isinstance(areas, str):
                    areas = [areas]
                if not isinstance(areas, list) or not areas:
                    continue

                alert_id = str(item.get("id") or f"oref-{time.time_ns()}")
                if not self._mark_and_filter(alert_id):
                    continue

                alerts.append(
                    Alert(
                        alert_id=alert_id,
                        threat=str(item.get("title") or "התרעה"),
                        areas=[str(x) for x in areas],
                        message=str(item.get("desc") or "היכנסו למרחב מוגן"),
                        source="oref",
                    )
                )
            return alerts

        return []


def format_alert(alert: Alert) -> str:
    eta = estimate_time(alert.areas)
    barrage = detect_barrage()
    prediction = predict_next_area(alert.areas)

    lines = [
        f"🚨 {alert.threat}",
        f"📍 אזורים: {', '.join(alert.areas[:12])}",
        f"⏱ זמן הגעה משוער: {eta} שניות",
    ]

    if barrage:
        lines.append("💥 זוהה רצף התרעות / מטח")

    if prediction:
        lines.append(f"⚠️ חיזוי: {prediction}")

    lines.append(f"🛰 מקור: {alert.source}")
    lines.append(f"📝 {alert.message}")

    return "\n".join(lines)