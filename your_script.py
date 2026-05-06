import requests
import numpy as np

LAT_RANGE = np.arange(24, 51, 2)
LON_RANGE = np.arange(-125, -66, 3)

TOP_K = 5

WEIGHTS = {
    "rain": 0.30,
    "wind": 0.30,
    "cloud": 0.15,
    "humidity": 0.10,
    "rotation": 0.15
}


def rotation_bonus(lat):
    return 465 * np.cos(np.radians(lat))


def normalize(x, xmin, xmax):
    return np.clip((x - xmin) / (xmax - xmin), 0, 1)


def base_score(rain, wind, cloud, humidity, lat):

    return (
        WEIGHTS["rain"] * (1 - normalize(rain, 0, 5)) +
        WEIGHTS["wind"] * (1 - normalize(wind, 0, 25)) +
        WEIGHTS["cloud"] * (1 - normalize(cloud, 0, 100)) +
        WEIGHTS["humidity"] * (1 - normalize(humidity, 0, 100)) +
        WEIGHTS["rotation"] * normalize(rotation_bonus(lat), 0, 465)
    ) * 100


def monte_carlo_score(rain, wind, cloud, humidity, lat, n=20):

    scores = []

    for _ in range(n):

        r = rain * np.random.normal(1, 0.1)
        w = wind * np.random.normal(1, 0.1)
        c = cloud * np.random.normal(1, 0.05)
        h = humidity * np.random.normal(1, 0.05)

        scores.append(base_score(r, w, c, h, lat))

    return float(np.mean(scores)), float(np.std(scores))


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


def analyze_location(lat, lon):

    data = get_weather_15d(lat, lon)

    if not data or "daily" not in data:
        return None

    best = None

    for i in range(len(data["daily"]["time"])):

        mean, risk = monte_carlo_score(
            data["daily"]["precipitation_sum"][i],
            data["daily"]["windspeed_10m_max"][i],
            data["daily"]["cloudcover_mean"][i],
            data["daily"]["relativehumidity_2m_mean"][i],
            lat
        )

        score = mean - (risk * 0.5)

        if best is None or score > best["score"]:
            best = {
                "lat": float(lat),
                "lon": float(lon),
                "date": data["daily"]["time"][i],
                "score": round(score, 2),
                "risk": round(risk, 2)
            }

    return best


def find_best_locations():

    results = []

    for lat in LAT_RANGE:
        for lon in LON_RANGE:
            res = analyze_location(lat, lon)
            if res:
                results.append(res)

    results.sort(key=lambda x: x["score"], reverse=True)

    return results[:TOP_K]
