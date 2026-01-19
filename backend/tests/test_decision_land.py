import asyncio
from pprint import pprint

from decision_engine import evaluate_property


async def test_land_purchase_fm_nagar():
    print("\n" + "=" * 80)
    print("TEST 3: LAND PURCHASE (FM Nagar, Balasore)")
    print("Use case: 6 dismil land for house construction (self-use)")
    print("=" * 80)

    # 1 dismil ≈ 435.6 sqft → 6 dismil ≈ 2613.6 sqft
    payload = {
        "address": "FM Nagar, Balasore, Odisha",
        "property_type": "land",
        "land_area_sqft": 6 * 435.6,
        "asking_price": 3_800_000,   # ₹38 Lakhs total
        "radius_m": 2000,
        "end_use": "self_use",

        # 🔑 CRITICAL: Road frontage input
        # Try changing this to 18, 25, 30, 35 to see behavior
        "road_width_ft": 30,
    }

    result = await evaluate_property(payload)
    pprint(result)


async def main():
    await test_land_purchase_fm_nagar()


if __name__ == "__main__":
    asyncio.run(main())
