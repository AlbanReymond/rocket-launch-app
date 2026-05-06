import requests
import numpy as np

# Résolution (on pourra raffiner plus tard)
LAT_RANGE = np.arange(-60, 61, 5)
LON_RANGE = np.arange(-180, 181, 10)

NB_TOP_RESULTS = 5


# -----------------------------
# PHYSIQUE SIMPLIFIÉE
# -----------------------------

def rotation_bonus(lat):
    # vitesse rotation Terre max équateur ~465 m/s
    return 465 * np.cos(np.radians(lat))


def normalize(x, xmin, xmax):
    if xmax - xmin == 0:
        return 0
    return np.clip((x - xmin) / (xmax - xmin), 0, 1)


# -----------------------------
# SCORE GLOBAL
# -----------------------------

def compute_score(p, w, c, h, lat):
    """
    Score global normalisé (0-100)
    """

    rain = 1 - normalize(p, 0, 5)
    wind = 1 - normalize(w, 0, 25)
    cloud = 1 - normalize(c, 0, 100)
    humidity = 1 - normalize(h, 0, 100)
    rotation = normalize(rotation_bonus(lat), 0, 465)

    score = (
        0.30 * rain +
        0.30 * wind +
        0.15 * cloud +
        0.10 * humidity +
        0.15 * rotation
    )

    return round(score * 100, 2)


# -----------------------------
# API METEO
# -----------------------------

def get_weather(lat, lon):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "precipitation,windspeed_10m,cloudcover,relativehumidity_2m",
        "forecast_days": 1
    }

    try:
        r = requests.get(url, params=params, timeout=5)
        return r.json()
    except:
        return None


# -----------------------------
# ANALYSE D'UN POINT
# -----------------------------

def analyze_location(lat, lon):
    data = get_weather(lat, lon)

    if not data or "hourly" not in data:
        return None

    best = None

    for i in range(len(data["hourly"]["time"])):

        score = compute_score(
            data["hourly"]["precipitation"][i],
            data["hourly"]["windspeed_10m"][i],
            data["hourly"]["cloudcover"][i],
            data["hourly"]["relativehumidity_2m"][i],
            lat
        )

        if best is None or score > best["score"]:
            best = {
                "lat": float(lat),
                "lon": float(lon),
                "time": data["hourly"]["time"][i],
                "score": score,
                "precip": data["hourly"]["precipitation"][i],
                "wind": data["hourly"]["windspeed_10m"][i],
                "cloud": data["hourly"]["cloudcover"][i],
                "humidity": data["hourly"]["relativehumidity_2m"][i]
            }

    return best


# -----------------------------
# OPTIMISATION GLOBALE
# -----------------------------

def find_best_locations():
    results = []

    for lat in LAT_RANGE:
        for lon in LON_RANGE:
            res = analyze_location(lat, lon)
            if res:
                results.append(res)

    results.sort(key=lambda x: x["score"], reverse=True)

    return results[:NB_TOP_RESULTS]
