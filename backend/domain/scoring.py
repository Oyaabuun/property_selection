def combine_scores(
    pricing,
    livability,
    access,
    commute,
    schools,
    flood,
    *,
    region_tier="tier_2_3",
    end_use="unspecified",
    road_liquidity: float = 1.0,   # ✅ NEW (1.0 = neutral)
):
    """
    India-aware, intent-aware scoring.

    Base score = weighted fundamentals
    Adjustments = intent + liquidity realism
    """

    # -------------------------
    # 1️⃣ Base regional weights
    # -------------------------
    if region_tier == "tier_1":
        weights = {
            "pricing": 0.25,
            "livability": 0.20,
            "flood": 0.15,
            "access": 0.15,
            "commute": 0.15,
            "schools": 0.10,
        }
    else:
        # Tier 2/3 → pricing + flood + schools matter more
        weights = {
            "pricing": 0.30,
            "livability": 0.15,
            "flood": 0.20,
            "access": 0.10,
            "commute": 0.10,
            "schools": 0.15,
        }

    base_score = (
        weights["pricing"] * pricing +
        weights["livability"] * livability +
        weights["flood"] * flood +
        weights["access"] * access +
        weights["commute"] * commute +
        weights["schools"] * schools
    )

    # -------------------------
    # 2️⃣ Intent-based adjustment
    # -------------------------
    adjustment = 0.0

    if end_use == "self_use":
        adjustment += 0.05 * schools
        adjustment += 0.05 * livability
        adjustment -= 0.05 * commute

        # Road access matters, but not dominant
        adjustment -= 0.03 * (road_liquidity - 1.0)

    elif end_use == "investment":
        adjustment += 0.05 * pricing
        adjustment -= 0.05 * access

        # Road access matters MORE for resale
        adjustment -= 0.08 * (road_liquidity - 1.0)

    # both / unspecified → moderate sensitivity
    else:
        adjustment -= 0.05 * (road_liquidity - 1.0)

    # -------------------------
    # 3️⃣ Liquidity sanity clamp
    # -------------------------
    final_score = base_score + adjustment

    return round(min(1.0, max(0.0, final_score)), 2)
