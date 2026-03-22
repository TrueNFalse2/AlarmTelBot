from flask import Flask, jsonify, render_template_string
from storage import alert_history

app = Flask(__name__)

# 📍 מיפוי בסיסי (אפשר להרחיב!)
CITY_COORDS = {
    "תל אביב": (32.0853, 34.7818),
    "אשקלון": (31.6688, 34.5743),
    "אשדוד": (31.8014, 34.6435),
    "שדרות": (31.525, 34.595),
    "ירושלים": (31.7683, 35.2137),
    "חיפה": (32.794, 34.9896),
    "נתניה": (32.3215, 34.8532),
    "באר שבע": (31.252, 34.7913),
    "קרית שמונה": (33.207, 35.572)
}

@app.route("/api/alerts")
def get_alerts():
    latest = []

    for alert in alert_history[-20:]:
        for city in alert.areas:
            if city in CITY_COORDS:
                lat, lon = CITY_COORDS[city]
                latest.append({
                    "city": city,
                    "lat": lat,
                    "lon": lon
                })

    return jsonify(latest)


@app.route("/")
def map_page():
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<title>🚨 Alert Map</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
<style>
#map { height: 100vh; }
</style>
</head>
<body>

<div id="map"></div>

<script>
var map = L.map('map').setView([31.5, 34.8], 7);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

var markers = [];

function loadAlerts() {
    fetch('/api/alerts')
    .then(res => res.json())
    .then(data => {
        markers.forEach(m => map.removeLayer(m));
        markers = [];

        data.forEach(a => {
            var m = L.circle([a.lat, a.lon], {
                radius: 10000,
                color: 'red'
            }).addTo(map)
            .bindPopup("🚨 " + a.city);

            markers.push(m);
        });
    });
}

setInterval(loadAlerts, 3000);
</script>

</body>
</html>
""")

def run_web():
    app.run(host="0.0.0.0", port=8000)