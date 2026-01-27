import asyncio
from pprint import pprint

from decision_engine import evaluate_property

'''
async def test_with_coordinates():
    print("\n" + "=" * 80)
    print("TEST 1: COORDINATES INPUT (Delhi-like)")
    print("=" * 80)

    payload = {
        "lat": 28.61,
        "lng": 77.23,
        "asking_price": 9_500_000,
        "property_type": "2bhk",
        "radius_m": 2000,
    }

    result = await evaluate_property(payload)
    pprint(result)

'''
async def test_with_address():
    print("\n" + "=" * 80)
    print("TEST 2: ADDRESS INPUT (Balasore, Odisha)")
    print("=" * 80)

    payload = {
        "address": "KOKILA ROYAL GARDEN, 6RP3+P54, Pokhariput, Bhubaneswar, Odisha 751020",
        "asking_price": 9_500_000,
        "property_type": "2bhk",
        "radius_m": 2000,
    }

    result = await evaluate_property(payload)
    pprint(result)


async def main():
    # IMPORTANT: run sequentially, same process, to detect leakage
    #await test_with_coordinates()
    await test_with_address()


if __name__ == "__main__":
    asyncio.run(main())
