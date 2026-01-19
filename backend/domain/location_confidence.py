def compute_location_confidence(signals: dict) -> float:
    score = 1.0

    if signals["pricing"]["score"] <= 0.5:
        score -= 0.15

    if signals["hospital_access"]["score"] < 0.3:
        score -= 0.2

    if signals["flood_risk"]["score"] < 0.5:
        score -= 0.15

    if "AQI data unavailable" in signals["air_quality"]["summary"]:
        score -= 0.1

    return round(max(0.4, score), 2)
