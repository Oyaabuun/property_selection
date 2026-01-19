import asyncio
from decision_engine import evaluate_property

async def main():
    result = await evaluate_property({
        "lat": 12.9352,     # try Bangalore
        "lng": 77.6245,
        "asking_price": 9500000,
        "property_type": "2bhk",
        "radius_m": 2000
    })
    print(result)

asyncio.run(main())
