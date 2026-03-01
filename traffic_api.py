import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("TOMTOM_API_KEY")

if not API_KEY:
    raise ValueError("TOMTOM_API_KEY not set. Please configure environment variable.")


def search_location(query):
    url = f"https://api.tomtom.com/search/2/geocode/{query}.json?key={API_KEY}"
    res = requests.get(url)
    data = res.json()

    if "results" not in data or len(data["results"]) == 0:
        return None, None, None

    result = data["results"][0]
    lat = result["position"]["lat"]
    lon = result["position"]["lon"]
    address = result["address"]["freeformAddress"]

    return lat, lon, address


def fetch_traffic(lat, lon):
    url = (
        "https://api.tomtom.com/traffic/services/4/"
        f"flowSegmentData/absolute/10/json?point={lat}%2C{lon}&unit=KMPH&key={API_KEY}"
    )

    res = requests.get(url)
    data = res.json()

    if "flowSegmentData" not in data:
        return None, None

    current_speed = data["flowSegmentData"]["currentSpeed"]
    free_speed = data["flowSegmentData"]["freeFlowSpeed"]

    return current_speed, free_speed
