# domain/livability.py
from data.aqi import fetch_aqi_signal

def normalize_india_aqi(aqi: int) -> int:
    """
    India realism guardrail.
    AQI < 30 is almost never realistic in Indian urban areas.
    """
    if aqi < 30:
        return 45
    return aqi


async def livability_signal(location: dict) -> dict:
    raw = await fetch_aqi_signal(location)

    if raw["details"].get("aqi") is None:
        return {
            "score": 0.5,
            "summary": "AQI data unavailable; assuming average Indian urban air quality",
            "details": {}
        }

    aqi = normalize_india_aqi(raw["details"]["aqi"])

    if aqi <= 50:
        score = 0.9
        label = "Good air quality (Indian context)"
    elif aqi <= 100:
        score = 0.7
        label = "Moderate air quality"
    elif aqi <= 200:
        score = 0.4
        label = "Poor air quality"
    else:
        score = 0.2
        label = "Very unhealthy air quality"

    return {
        "score": score,
        "summary": f"AQI ~{aqi} ({label})",
        "details": {
            "aqi": aqi,
            "category": label,
            "dominant_pollutant": raw["details"].get("dominant_pollutant")
        }
    }
