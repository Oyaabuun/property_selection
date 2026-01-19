import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from data.geocode import resolve_location

async def test():
    address = "MG Road, Bangalore"
    print(f"Resolving: {address}")
    result = await resolve_location(address=address)
    print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(test())
