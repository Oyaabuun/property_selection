import asyncio
from data.geocode import resolve_location

async def test():
    loc1 = await resolve_location(
        address="Prestige Shantiniketan, Whitefield, Bangalore"
    )
    print("Address →", loc1)

    loc2 = await resolve_location(
        lat=12.9352,
        lng=77.6245
    )
    print("Lat/Lng →", loc2)

asyncio.run(test())
