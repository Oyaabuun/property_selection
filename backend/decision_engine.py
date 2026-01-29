from domain.pricing import price_signal
from domain.scoring import combine_scores
from utils.human_summary import build_human_summary
from data.geocode import resolve_location
from domain.location_confidence import compute_location_confidence
from domain.region import infer_region_tier
from domain.road_access import road_access_signal

from llm_reasoner import reason_with_llm

from data.maps import (
    hospital_access_signal,
    commute_stress_signal,
    school_density_signal,
    flood_risk_signal,
)
from data.aqi import fetch_aqi_signal


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

DECISION_BANDS = {
    "BUY": 0.7,
    "CAUTION": 0.5,
}

MAX_LLM_DEVIATION = 0.15

def normalize_pricing_signal(pricing: dict) -> dict:
    if pricing["details"].get("pricing_basis") == "no_comparables":
        pricing["score"] = min(pricing["score"], 0.45)
        pricing["summary"] = (
            pricing["summary"].rstrip(".")
            + ". Absence of transaction data increases valuation risk and resale uncertainty."
        )

    return pricing

def contextualize_signal(signal: dict, context: str) -> dict:
    summary = signal.get("summary", "")

    if context == "hospital" and signal["score"] < 0.4:
        summary += " This reflects typical infrastructure gaps in Tier 2/3 regions."

    if context == "air_quality":
        if signal["score"] >= 0.7:
            summary += " This is typical across many Indian cities."
        elif signal["score"] < 0.5:
            summary += " Sensitive individuals may experience discomfort."

    if context == "schools" and signal["score"] >= 0.7:
        summary += " This supports family end-use suitability."

    signal["summary"] = summary
    return signal

def enforce_decision_band(numeric_score: float, llm_decision: dict) -> dict:
    if numeric_score >= DECISION_BANDS["BUY"]:
        llm_decision["decision"] = "BUY"
    elif numeric_score >= DECISION_BANDS["CAUTION"]:
        llm_decision["decision"] = "CAUTION"
    else:
        llm_decision["decision"] = "AVOID"
    return llm_decision

def derive_reference_hub(location: dict) -> dict:
    return {
        "lat": location["lat"],
        "lng": location["lng"],
        "label": "local employment cluster (approximate)",
    }


def calibrate_confidence(llm_conf: float, numeric_score: float) -> float:
    """
    Confidence reflects reliability of the assessment,
    not attractiveness of the property.
    """
    base = min(llm_conf, numeric_score)

    # Penalize uncertainty zones
    if numeric_score < 0.6:
        base -= 0.05

    if numeric_score < 0.5:
        base -= 0.1

    return round(max(0.3, min(base, 0.7)), 2)



def soften_recommendation(text: str, region_tier: str) -> str:
    if region_tier == "tier_2_3":
        replacements = {
            "Extreme overvaluation": "Aggressive pricing",
            "Reject the proposal": "Proceed only with strong negotiation",
            "fundamentally decoupled": "misaligned",
            "unsafe investment": "higher-risk entry",
        }
        for k, v in replacements.items():
            text = text.replace(k, v)
    return text

def normalize_recommendation_by_decision(
    decision: str,
    recommendation: str,
) -> str:
    if decision == "CAUTION":
        hard_phrases = [
            "Reject the current proposal",
            "Reject the proposal",
            "Do not proceed",
            "Capital preservation is at risk",
            "unsafe investment",
        ]

        for phrase in hard_phrases:
            recommendation = recommendation.replace(
                phrase,
                "Proceed only with significant negotiation and safeguards",
            )

        if not recommendation.lower().startswith("this property requires caution"):
            recommendation = "This property requires caution. " + recommendation

    if decision == "BUY":
        recommendation = recommendation.replace(
            "Proceed only",
            "Proceed confidently"
        )

    return recommendation



def derive_buy_conditions(signals: dict) -> list[str]:
    conditions = []

    if signals["pricing"]["score"] < 0.6:
        conditions.append("Price reduction of 15–20% from current asking")

    if signals["hospital_access"]["score"] < 0.4:
        conditions.append(
            "Emergency hospital access within 25–30 minutes or verified medical tie-up"
        )

    if signals["flood_risk"]["score"] < 0.5:
        conditions.append(
            "Site-level drainage and elevation verification before purchase"
        )

    if not conditions:
        conditions.append("No major blockers identified at current valuation")

    return conditions


def derive_positive_factors(signals: dict) -> list[str]:
    positives = []

    if signals["school_access"]["score"] >= 0.8:
        positives.append("Strong school ecosystem suitable for family living")

    if signals["flood_risk"]["score"] >= 0.6:
        positives.append("No major flood vulnerability observed")

    if signals["air_quality"]["score"] >= 0.7:
        positives.append("Acceptable air quality by Indian urban standards")

    return positives


def derive_buyer_profile(signals: dict, end_use: str) -> dict:
    buy, avoid = [], []

    if signals["school_access"]["score"] >= 0.8:
        buy.append("Families prioritizing education access")

    if signals["pricing"]["score"] < 0.6:
        avoid.append("Buyers unwilling to negotiate on price")

    if signals["hospital_access"]["score"] < 0.4:
        avoid.append("Elderly buyers or households with medical dependency")

    if end_use in {"investment", "both"} and signals["pricing"]["score"] < 0.6:
        avoid.append("Short-term investors seeking quick liquidity")

    if not buy:
        buy.append("Buyers comfortable with Tier 2/3 infrastructure trade-offs")

    return {
        "suitable_for": buy,
        "not_suitable_for": avoid,
    }

def append_caution_closure(decision: str, recommendation: str) -> str:
    if decision != "CAUTION":
        return recommendation

    if "does not rule out the property entirely" in recommendation:
        return recommendation

    return recommendation + (
        " This assessment does not rule out the property entirely; "
        "it indicates that proceeding only makes sense if the price "
        "corrects materially or if key infrastructure risks are mitigated."
    )

def assert_recommendation_consistency(decision: str, recommendation: str):
    if decision == "CAUTION":
        forbidden = ["reject", "avoid", "capital trap", "do not proceed"]
        if any(word in recommendation.lower() for word in forbidden):
            raise ValueError(
                "Recommendation tone exceeds CAUTION severity"
            )

# -------------------------------------------------------------------
# Main Engine
# -------------------------------------------------------------------

async def evaluate_property(data: dict) -> dict:
    with open("debug_log.txt", "a") as f:
        f.write(f"\nDEBUG: evaluate_property received data: {data}\n")
    
    location = await resolve_location(
        address=data.get("address"),
        lat=data.get("lat"),
        lng=data.get("lng"),
    )
    
    with open("debug_log.txt", "a") as f:
        f.write(f"DEBUG: resolved location: {location}\n")

    if not location.get("lat") or not location.get("lng"):
        return {
            "decision": "CAUTION",
            "confidence": 0.3,
            "numeric_score": 0.3,
            "summary": "Location could not be resolved accurately.",
            "signals": {"location_resolution": location},
        }

    region = infer_region_tier(location)

    end_use = data.get("end_use", "both")
    if end_use not in {"self_use", "investment", "both"}:
        end_use = "both"

    pricing = await price_signal(
        location=location,
        asking_price=data["asking_price"],
        property_type=data.get("property_type", "unknown"),
        radius_m=data.get("radius_m", 2000),
        land_area_sqft=data.get("land_area_sqft"),
        region_tier=region["tier"],
    )
    pricing = normalize_pricing_signal(pricing)

    road_access = await road_access_signal(
        location,
        user_road_width_ft=data.get("road_width_ft")
    )

    # -------------------------
    # Apply road frontage effect to LAND pricing
    # -------------------------
    if data.get("property_type") in {"land", "plot"}:
        multiplier = road_access.get("price_multiplier", 1.0)

        if "recommended_band" in pricing.get("details", {}):
            band = pricing["details"]["recommended_band"]

            pricing["details"]["recommended_band"] = {
                "low": int(band["low"] * multiplier),
                "mid": int(band["mid"] * multiplier),
                "high": int(band["high"] * multiplier),
            }

            pricing["summary"] += (
                f" Road frontage adjustment applied "
                f"(×{multiplier:.2f}) based on access width."
            )

    air_quality = contextualize_signal(
        await fetch_aqi_signal(location), "air_quality"
    )
    hospital = contextualize_signal(
        await hospital_access_signal(location), "hospital"
    )
    schools = contextualize_signal(
        await school_density_signal(location), "schools"
    )
    flood = await flood_risk_signal(location)

    commute = await commute_stress_signal(
        home=location,
        work_hub=derive_reference_hub(location),
    )
    commute["details"]["assumption"] = "Approximate local commute estimate."

    road_liquidity = road_access["liquidity_factor"]

    

    numeric_score = combine_scores(
        pricing=pricing["score"],
        livability=air_quality["score"],
        access=hospital["score"],
        commute=commute["score"],
        schools=schools["score"],
        flood=flood["score"],
        region_tier=region["tier"],
        end_use=end_use,
        road_liquidity=road_liquidity,  # ✅ NEW
    )


    context = {
        "asking_price": data["asking_price"],
        "property_type": data.get("property_type"),
        "end_use": end_use,
        "region": region,
        "location": location,
        "signals": {
            "pricing": pricing,
            "road_access": road_access,
            "air_quality": air_quality,
            "hospital_access": hospital,
            "commute_stress": commute,
            "school_access": schools,
            "flood_risk": flood,
        },
    }

    llm_decision = await reason_with_llm(context, numeric_score)

    llm_decision["confidence"] = calibrate_confidence(
        llm_decision["confidence"], numeric_score
    )

    llm_decision = enforce_decision_band(numeric_score, llm_decision)

    llm_decision["recommendation"] = soften_recommendation(
        llm_decision.get("recommendation", ""), region["tier"]
    )

    llm_decision["recommendation"] = normalize_recommendation_by_decision(
        llm_decision["decision"],
        llm_decision["recommendation"],
    )

    llm_decision["recommendation"] = append_caution_closure(
        llm_decision["decision"],
        llm_decision["recommendation"],
    )

    assert_recommendation_consistency(
        llm_decision["decision"],
        llm_decision["recommendation"],
    )


    return {
        **llm_decision,
        "numeric_score": numeric_score,
        "summary": build_human_summary(context["signals"]),
        "signals": context["signals"],
        "location_confidence": compute_location_confidence(context["signals"]),
        "region": region,
        "end_use_assumed": end_use,
        "positive_factors": derive_positive_factors(context["signals"]),
        "buy_conditions": derive_buy_conditions(context["signals"]),
        "buyer_profile": derive_buyer_profile(context["signals"], end_use),
        
    }
