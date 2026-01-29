def infer_region_tier(location: dict) -> dict:
    """
    Very conservative India-first tier inference.
    No LLM, no guessing.
    """
    lat, lng = location["lat"], location["lng"]

    # Tier-1 metro bounding boxes (approx, safe)
    if 28.4 <= lat <= 28.9 and 76.8 <= lng <= 77.4:
        return {"tier": "tier_1", "label": "Delhi NCR"}
    if 12.8 <= lat <= 13.2 and 77.4 <= lng <= 77.8:
        return {"tier": "tier_1", "label": "Bengaluru"}
    if 18.8 <= lat <= 19.3 and 72.7 <= lng <= 73.1:
        return {"tier": "tier_1", "label": "Mumbai"}

    # Everything else = Tier 2/3 for now
    return {"tier": "tier_2_3", "label": "Non-metro India"}
