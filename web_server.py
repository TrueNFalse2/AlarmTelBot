from flask import Flask, jsonify, render_template_string
from storage import alert_history

app = Flask(__name__)

# 🔥 מפת ערים (אפשר להרחיב!)
CITY_COORDS = {
    "תל אביב": (32.0853, 34.7818),
    "אשקלון": (31.6688, 34.5743),
    "אשדוד": (31.8014, 34.6435),
    "שדרות": (31.525, 34.595),
    "ירושלים": (31.7683, 35.2137),
    "חיפה": (32.794, 34.9896),
    "נתניה": (32.3215, 34.8532),
    "באר שבע": (31.252, 34.7913),
    "קרית שמונה": (33.207, 35.572),
    "הרצליה": (32.1663, 34.8435),
    "רעננה": (32.1848, 34.8713),
    "כפר סבא": (32.1782, 34.9076),
    "חולון": (32.0158, 34.7874),
    "בת ים": (32.0238, 34.7519)
}

@app.route("/api/heatmap")
def heatmap_data():
    points = []

    for alert in alert_history[-50:]:
        for city in alert.areas:
            if city in CITY_COORDS:
                lat, lon = CITY_COORDS[city]
                points.append([lat, lon, 1])  # weight

    return jsonify(points)


@app.route("/")
def map_page():
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<title>🔥 Live Heatmap</title>

<link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet.heat/dist/leaflet-heat.js"></script>

<style>
#map { height: 100vh; }
</style>
</head>
<body>

<div id="map"></div>

<script>
var map = L.map('map').setView([31.5, 34.8], 7);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

var heatLayer = L.heatLayer([], {
    radius: 25,
    blur: 15,
    maxZoom: 10,
    gradient: {
        0.2: 'blue',
        0.4: 'lime',
        0.6: 'yellow',
        0.8: 'orange',
        1.0: 'red'
    }
}).addTo(map);

function loadHeatmap() {
    fetch('/api/heatmap')
    .then(res => res.json())
    .then(data => {
        heatLayer.setLatLngs(data);

        // 🔥 זום אוטומטי לאזור חם
        if (data.length > 0) {
            var last = data[data.length - 1];
            map.setView([last[0], last[1]], 9);
        }
    });
}

setInterval(loadHeatmap, 3000);
</script>

</body>
</html>
""")

def run_web():
    app.run(host="0.0.0.0", port=8000)