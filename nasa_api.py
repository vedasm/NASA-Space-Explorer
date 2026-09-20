# System Imports
import os
import time
from datetime import date

# API Imports
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("NASA_API_KEY", "TEST_KEY")
TIMEOUT = 10

session = requests.Session()
_cache = {}

def _cached(key, ttl_seconds, loader):
    cached_entry = _cache.get(key)
    if cached_entry and time.time() - cached_entry["stored_at"] < ttl_seconds:
        return cached_entry["value"]

    value = loader()
    _cache[key] = {"value": value, "stored_at": time.time()}
    return value

def _get(url, params):
    params = dict(params, api_key=API_KEY)
    response = session.get(url, params=params, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()

def _fetch_apod():
    data = _get("https://api.nasa.gov/planetary/apod", {})
    return {
        "title": data.get("title", "Untitled"),
        "explanation": data.get("explanation", ""),
        "url": data.get("url", ""),
        "hdurl": data.get("hdurl"),
        "media_type": data.get("media_type", "image"),
        "date": data.get("date", ""),
        "copyright": data.get("copyright"),
    }

def get_apod():
    return _cached("apod", 3600, _fetch_apod)

def _fetch_asteroids():
    today = date.today().isoformat()
    data = _get(
        "https://api.nasa.gov/neo/rest/v1/feed",
        {"start_date": today, "end_date": today},
    )

    raw = [item for items in data.get("near_earth_objects", {}).values() for item in items]
    asteroids = []
    for item in raw:
        approach = (item.get("close_approach_data") or [{}])[0]
        asteroids.append(
            {
                "id": item.get("id"),
                "name": item.get("name", "").strip("()"),
                "hazardous": item.get("is_potentially_hazardous_asteroid", False),
                "diameter_m": item["estimated_diameter"]["meters"]["estimated_diameter_max"],
                "miss_distance_km": float(
                    approach.get("miss_distance", {}).get("kilometers", 0)
                ),
                "velocity_kph": float(
                    approach.get("relative_velocity", {}).get(
                        "kilometers_per_hour", 0
                    )
                ),
                "approach_time": approach.get("close_approach_date_full", ""),
                "url": item.get("nasa_jpl_url"),
            }
        )

    asteroids.sort(key=lambda asteroid: asteroid["miss_distance_km"])
    return {"date": today, "count": len(asteroids), "asteroids": asteroids}

def _fetch_epic_images(selected_date):
    data = _get(f"https://api.nasa.gov/EPIC/api/natural/date/{selected_date}", {})
    year, month, day = selected_date.split("-")
    return [
        {
            "name": item["image"],
            "caption": item.get("caption", ""),
            "timestamp": item.get("date", ""),
            "url": (
                "https://epic.gsfc.nasa.gov/archive/natural/"
                f"{year}/{month}/{day}/png/{item['image']}.png"
            ),
        }
        for item in data
    ]

def get_epic_images(selected_date):
    return _cached(
        f"epic:{selected_date}", 86400, lambda: _fetch_epic_images(selected_date)
    )

def get_asteroids():
    return _cached("asteroids", 3600, _fetch_asteroids)