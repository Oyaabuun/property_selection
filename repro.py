import httpx
import asyncio
import json

async def test():
    url = "http://localhost:8000/decision"
    payload = {
        "address": "MG Road, Bangalore",
        "asking_price": 10000000,
        "property_type": "3bhk",
        "radius_m": 2000
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, timeout=20)
            print(f"Status: {response.status_code}")
            print(json.dumps(response.json(), indent=2))
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
