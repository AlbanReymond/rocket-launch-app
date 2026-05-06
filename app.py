from flask import Flask, jsonify, render_template_string
import threading
import time
from your_script import find_best_locations

app = Flask(__name__)

cache = {
    "top_sites": [],
    "best_launch_window": None
}

last_update = None
lock = threading.Lock()

UPDATE_INTERVAL = 300


# -----------------------------
# BACKGROUND UPDATE
# -----------------------------

def updater():

    global cache, last_update

    while True:
        start = time.time()

        try:
            print("🧠 IA computing best launch windows...")

            new_data = find_best_locations()

            with lock:
                cache = new_data
                last_update = time.strftime("%Y-%m-%d %H:%M:%S")

            print("✅ AI update done")

        except Exception as e:
            print("❌ Error:", e)

        time.sleep(max(0, UPDATE_INTERVAL - (time.time() - start)))


threading.Thread(target=updater, daemon=True).start()


# -----------------------------
# API
# -----------------------------

@app.route("/data")
def data():
    with lock:
        return jsonify({
            "last_update": last_update,
            "top_sites": cache["top_sites"],
            "best_launch_window": cache["best_launch_window"]
        })


# -----------------------------
# 🌍 CESIUM 3D GLOBE
# -----------------------------

HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>AI Launch Window Optimizer</title>
  <script src="https://cesium.com/downloads/cesiumjs/releases/1.113/Build/Cesium/Cesium.js"></script>
  <link href="https://cesium.com/downloads/cesiumjs/releases/1.113/Build/Cesium/Widgets/widgets.css" rel="stylesheet">
  <style>
    html, body, #cesiumContainer { width:100%; height:100%; margin:0; padding:0; overflow:hidden; }
  </style>
</head>

<body>
<div id="cesiumContainer"></div>

<script>
const viewer = new Cesium.Viewer('cesiumContainer', {
    terrainProvider: Cesium.createWorldTerrain()
});

async function loadData() {

    const res = await fetch('/data');
    const data = await res.json();

    viewer.entities.removeAll();

    // TOP 5 sites
    data.top_sites.forEach(p => {
        viewer.entities.add({
            position: Cesium.Cartesian3.fromDegrees(p.lon, p.lat),
            point: { pixelSize: 12, color: Cesium.Color.RED },
            label: {
                text: "Score: " + p.score,
                font: "14px sans-serif"
            }
        });
    });

    // BEST LAUNCH WINDOW (highlight gold)
    if (data.best_launch_window) {
        const b = data.best_launch_window;

        viewer.entities.add({
            position: Cesium.Cartesian3.fromDegrees(b.lon, b.lat),
            point: { pixelSize: 18, color: Cesium.Color.GOLD },
            label: {
                text: "🔥 BEST WINDOW " + b.date,
                font: "16px sans-serif",
                fillColor: Cesium.Color.YELLOW
            }
        });
    }
}

setInterval(loadData, 5000);
loadData();

</script>
</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(HTML)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
