from data.repositories import get_transactions
from statistics import median

DISMIL_SQFT = 435.6


async def price_signal(
    location: dict,
    asking_price: float,
    property_type: str,
    radius_m: int,
    *,
    land_area_sqft: float | None = None,
    region_tier: str = "tier_2_3",
) -> dict:
    """
    Unified pricing logic for:
    - Flats / houses → transaction comparison
    - Land → ₹ per dismil negotiation band
    """

    # -------------------------
    # LAND / PLOT PRICING
    # -------------------------
    if property_type in {"land", "plot"}:
        land = estimate_land_rate_per_dismil(
            asking_price=asking_price,
            land_area_sqft=land_area_sqft,
            region_tier=region_tier,
        )

        return {
            "score": land["score"],
            "summary": land["summary"],
            "details": {
                "asking_rate_per_dismil": land["asking_rate_per_dismil"],
                "recommended_band": land["recommended_band"],
                "pricing_basis": "heuristic_land_band",
                "confidence_note": land["confidence_note"],
                "liquidity_note": (
                    "Land resale liquidity is typically lower in Tier 2/3 regions"
                    if region_tier == "tier_2_3"
                    else "Land liquidity is generally stronger in metro regions"
                ),
            },
        }

    # -------------------------
    # BUILT-UP PROPERTY PRICING
    # -------------------------
    try:
        txns = await get_transactions(location, property_type, radius_m)
    except Exception:
        txns = []

    if not txns:
        return {
            "score": 0.5,
            "summary": "Insufficient transaction data; pricing confidence is low",
            "details": {
                "pricing_basis": "no_comparables",
                "confidence_note": "Low confidence due to lack of recent transactions",
            },
        }

    avg_price = sum(t["price"] for t in txns) / len(txns)
    diff_pct = (asking_price - avg_price) / avg_price
    abs_diff = abs(diff_pct)

    if abs_diff <= 0.15:
        score = 0.85
    elif abs_diff <= 0.35:
        score = 0.65
    else:
        score = 0.4

    if len(txns) < 5:
        score -= 0.1

    score = max(0.0, min(1.0, score))
    direction = "above" if diff_pct > 0 else "below"

    return {
        "score": round(score, 2),
        "summary": (
            f"Asking price is {abs(diff_pct)*100:.1f}% {direction} "
            f"the local average based on {len(txns)} recent transactions"
        ),
        "details": {
            "local_avg_price": round(avg_price),
            "difference_pct": round(diff_pct * 100, 1),
            "transaction_count": len(txns),
            "pricing_basis": "transaction_comparison",
            "confidence_note": (
                "Pricing confidence is moderate due to limited transaction volume"
                if len(txns) < 5
                else "Pricing confidence is high"
            ),
        },
    }


def estimate_land_rate_per_dismil(
    asking_price: float,
    land_area_sqft: float | None,
    region_tier: str,
) -> dict:
    if not land_area_sqft:
        return {
            "score": 0.45,
            "asking_rate_per_dismil": None,
            "recommended_band": None,
            "confidence_note": "Land area not provided; unable to estimate rate",
            "summary": "Land area not provided; pricing assessment is incomplete",
        }

    dismil = land_area_sqft / DISMIL_SQFT
    asking_rate = asking_price / dismil

    # -------------------------
    # INDIA-REALISTIC BASE BAND
    # -------------------------
    if region_tier == "tier_1":
        base_low, base_high = 6_00_000, 25_00_000
    else:
        base_low, base_high = 2_00_000, 6_00_000

    base_mid = (base_low + base_high) / 2

    # Liquidity compression for Tier 2/3
    if region_tier == "tier_2_3":
        base_high *= 0.95

    recommended_band = {
        "low": round(base_low),
        "mid": round(base_mid),
        "high": round(base_high),
    }

    # -------------------------
    # SCORE LOGIC
    # -------------------------
    if asking_rate <= base_mid:
        score = 0.7
        verdict = "falls within a reasonable negotiation range"
    elif asking_rate <= base_high:
        score = 0.55
        verdict = "is priced toward the higher end of the local range"
    else:
        score = 0.35
        verdict = "appears aggressively priced for this locality"

    return {
        "score": round(score, 2),
        "asking_rate_per_dismil": round(asking_rate),
        "recommended_band": recommended_band,
        "confidence_note": (
            "Derived from regional heuristics and liquidity patterns; "
            "exact transaction data is unavailable"
        ),
        "summary": (
            f"Asking land rate is ₹{asking_rate:,.0f} per dismil, which {verdict}. "
            f"A practical negotiation range is ₹{base_low:,.0f}–₹{base_high:,.0f} "
            f"per dismil for a {region_tier.replace('_', ' ')} market."
        ),
    }
