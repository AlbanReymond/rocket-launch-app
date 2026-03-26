from flask import Flask, jsonify
import threading
import time
from your_script import find_best_locations

app = Flask(__name__)

data_cache = []
last_update = None

def update_data():
    global data_cache, last_update
    while True:
        try:
            print("🔄 Mise à jour...")
            data_cache = find_best_locations()
            last_update = time.strftime("%Y-%m-%d %H:%M:%S")
            print("✅ OK")
        except Exception as e:
            print("❌ Erreur :", e)

        time.sleep(300)

threading.Thread(target=update_data, daemon=True).start()

@app.route("/")
def home():
    return {
        "status": "🚀 API running",
        "last_update": last_update
    }

@app.route("/data")
def data():
    return jsonify({
        "last_update": last_update,
        "results": data_cache
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
