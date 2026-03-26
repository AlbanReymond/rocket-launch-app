import requests
import numpy as np

LAT_RANGE = np.arange(-25, 26, 5)
LON_RANGE = np.arange(-180, 181, 10)
NB_TOP_RESULTS = 10

def compute_score(p, w, c, h):
    score = 100
    score -= p * 15
    score -= w * 2
    score -= c * 0.5
    score -= h * 0.2
    return max(score, 0)

def get_weather(lat, lon):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "precipitation,windspeed_10m,cloudcover,relativehumidity_2m",
        "forecast_days": 7
    }
    try:
        return requests.get(url, params=params, timeout=5).json()
    except:
        return None

def analyze_location(lat, lon):
    data = get_weather(lat, lon)
    if not data or "hourly" not in data:
        return None

    best = None

    for t, p, w, c, h in zip(
        data["hourly"]["time"],
        data["hourly"]["precipitation"],
        data["hourly"]["windspeed_10m"],
        data["hourly"]["cloudcover"],
        data["hourly"]["relativehumidity_2m"]
    ):
        score = compute_score(p, w, c, h)

        if best is None or score > best["score"]:
            best = {
                "lat": float(lat),
                "lon": float(lon),
                "time": t,
                "score": float(score),
                "precip": float(p),
                "wind": float(w),
                "cloud": float(c),
                "humidity": float(h)
            }

    return best

def find_best_locations():
    results = []

    for lat in LAT_RANGE:
        for lon in LON_RANGE:
            res = analyze_location(lat, lon)
            if res:
                results.append(res)

    results = sorted(results, key=lambda x: x["score"], reverse=True)
    return results[:NB_TOP_RESULTS]
