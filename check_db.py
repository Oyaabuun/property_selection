from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def check_db():
    client = AsyncIOMotorClient(os.getenv("MONGO_URI"))
    db = client[os.getenv("DB_NAME")]
    
    print("--- Locations ---")
    async for doc in db.locations.find():
        print(doc)
        
    print("\n--- Signals Cache ---")
    async for doc in db.signals_cache.find():
        print(doc)

if __name__ == "__main__":
    asyncio.run(check_db())
