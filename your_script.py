import requests
import numpy as np

LAT_RANGE = np.arange(24, 51, 2)
LON_RANGE = np.arange(-125, -66, 3)

TOP_K = 5


# -----------------------------
# PHYSIQUE (rotation terrestre)
# -----------------------------

def rotation_bonus(lat):
    return 465 * np.cos(np.radians(lat))


def normalize(x, xmin, xmax):
    return np.clip((x - xmin) / (xmax - xmin), 0, 1)


# -----------------------------
# SCORE MÉTÉO
# -----------------------------

def compute_score(rain, wind, cloud, humidity, lat):
    rain_s = 1 - normalize(rain, 0, 5)
    wind_s = 1 - normalize(wind, 0, 25)
    cloud_s = 1 - normalize(cloud, 0, 100)
    hum_s = 1 - normalize(humidity, 0, 100)
    rot_s = normalize(rotation_bonus(lat), 0, 465)

    score = (
        0.30 * rain_s +
        0.30 * wind_s +
        0.15 * cloud_s +
        0.10 * hum_s +
        0.15 * rot_s
    )

    return score * 100


# -----------------------------
# METEO 15 JOURS
# -----------------------------

def get_weather_15d(lat, lon):
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "precipitation_sum,windspeed_10m_max,cloudcover_mean,relativehumidity_2m_mean",
        "forecast_days": 15
    }

    try:
        return requests.get(url, params=params, timeout=6).json()
    except:
        return None


# -----------------------------
# ANALYSE D'UN SITE
# -----------------------------

def analyze_location(lat, lon):
    data = get_weather_15d(lat, lon)

    if not data or "daily" not in data:
        return None

    best = None

    for i in range(len(data["daily"]["time"])):

        score = compute_score(
            data["daily"]["precipitation_sum"][i],
            data["daily"]["windspeed_10m_max"][i],
            data["daily"]["cloudcover_mean"][i],
            data["daily"]["relativehumidity_2m_mean"][i],
            lat
        )

        if best is None or score > best["score"]:
            best = {
                "lat": float(lat),
                "lon": float(lon),
                "date": data["daily"]["time"][i],
                "score": round(score, 2)
            }

    return best


# -----------------------------
# 🧠 “IA” DE SELECTION DE LAUNCH WINDOW
# -----------------------------
# logique : cherche la meilleure combinaison (lieu + jour)

def find_best_launch_window(all_results):
    """
    pseudo IA :
    - trie globalement tous les points temporels
    - détecte meilleure fenêtre globale
    """

    if not all_results:
        return None

    # tri global (tous sites + toutes dates)
    best = max(all_results, key=lambda x: x["score"])

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

    top_sites = results[:TOP_K]

    best_launch_window = find_best_launch_window(top_sites)

    return {
        "top_sites": top_sites,
        "best_launch_window": best_launch_window
    }
