def build_human_summary(signals: dict) -> str:
    reasons = []

    # Hospital
    h = signals["hospital_access"]
    if h["score"] < 0.4:
        reasons.append(
            "limited emergency medical access"
        )

    # Schools
    s = signals["school_access"]
    if s["score"] < 0.4:
        reasons.append(
            "poor availability of schools within daily travel range"
        )

    # Flood
    f = signals["flood_risk"]
    if f["score"] <= 0.4:
        reasons.append(
            "elevated or uncertain flood risk during heavy rains"
        )

    # AQI
    a = signals["air_quality"]
    if a["score"] <= 0.4:
        reasons.append(
            "suboptimal air quality affecting long-term health"
        )

    # Commute
    c = signals["commute_stress"]
    if c["score"] <= 0.4:
        reasons.append(
            "high daily commute burden"
        )

    if not reasons:
        return (
            "Based on available data, the property meets most baseline livability "
            "criteria and does not show any major red flags for long-term residential use."
        )

    return (
        "Key concerns include "
        + ", ".join(reasons)
        + ". These factors may negatively impact daily living comfort, "
          "long-term usability, and resale demand."
    )
