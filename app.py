from flask import Flask, jsonify
import threading
import time
from your_script import find_best_locations

app = Flask(__name__)

cache = []
last_update = None
lock = threading.Lock()

UPDATE_INTERVAL = 300


# -----------------------------
# BACKGROUND UPDATER
# -----------------------------

def updater():
    global cache, last_update

    while True:
        start = time.time()

        try:
            print("🔄 Calcul top sites de lancement...")

            new_data = find_best_locations()

            with lock:
                cache = new_data
                last_update = time.strftime("%Y-%m-%d %H:%M:%S")

            print("✅ Update OK")

        except Exception as e:
            print("❌ Error:", e)

        elapsed = time.time() - start
        time.sleep(max(0, UPDATE_INTERVAL - elapsed))


threading.Thread(target=updater, daemon=True).start()


# -----------------------------
# ROUTES API
# -----------------------------

@app.route("/")
def home():
    with lock:
        return jsonify({
            "status": "🚀 Launch Optimizer Running",
            "last_update": last_update,
            "top_sites_count": len(cache)
        })


@app.route("/data")
def data():
    with lock:
        return jsonify({
            "last_update": last_update,
            "top_5_launch_sites": cache
        })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
