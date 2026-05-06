from flask import Flask, jsonify, render_template_string
import threading
import time
from your_script import find_best_locations

app = Flask(__name__)

cache = []
last_update = None
lock = threading.Lock()

UPDATE_INTERVAL = 300


def updater():

    global cache, last_update

    while True:

        start = time.time()

        try:
            print("🧠 AI computing 3D launch windows...")

            new_data = find_best_locations()

            with lock:
                cache = new_data
                last_update = time.strftime("%Y-%m-%d %H:%M:%S")

            print("✅ Updated")

        except Exception as e:
            print("❌", e)

        time.sleep(max(0, UPDATE_INTERVAL - (time.time() - start)))


threading.Thread(target=updater, daemon=True).start()


@app.route("/data")
def data():

    with lock:
        return jsonify({
            "last_update": last_update,
            "top_sites": cache
        })


# -----------------------------
# 🌍 CESIUM 3D GLOBE (Google Earth style)
# -----------------------------

HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>🌍 AI Launch 3D Globe</title>

  <script src="https://cesium.com/downloads/cesiumjs/releases/1.113/Build/Cesium/Cesium.js"></script>
  <link href="https://cesium.com/downloads/cesiumjs/releases/1.113/Build/Cesium/Widgets/widgets.css" rel="stylesheet">

  <style>
    html, body, #globe {
      width: 100%;
      height: 100%;
      margin: 0;
      overflow: hidden;
    }
  </style>
</head>

<body>
<div id="globe"></div>

<script>
const viewer = new Cesium.Viewer('globe', {
    terrainProvider: Cesium.createWorldTerrain()
});

async function updateGlobe() {

    const res = await fetch('/data');
    const data = await res.json();

    viewer.entities.removeAll();

    data.top_sites.forEach(p => {

        viewer.entities.add({
            position: Cesium.Cartesian3.fromDegrees(p.lon, p.lat),
            point: {
                pixelSize: 14,
                color: Cesium.Color.RED
            },
            label: {
                text: `Score: ${p.score}\\nRisk: ${p.risk}\\n${p.date}`,
                font: "14px sans-serif",
                fillColor: Cesium.Color.WHITE
            }
        });

    });

}

setInterval(updateGlobe, 5000);
updateGlobe();

</script>
</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(HTML)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
