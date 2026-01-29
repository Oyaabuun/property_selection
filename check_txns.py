from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import os
from dotenv import load_dotenv

# Path to .env relative to current dir
dotenv_path = "backend/.env"
load_dotenv(dotenv_path)

async def check_transactions():
    mongo_uri = os.getenv("MONGO_URI")
    db_name = os.getenv("DB_NAME")
    
    if not mongo_uri or not db_name:
        print("Missing env vars")
        return

    client = AsyncIOMotorClient(mongo_uri)
    db = client[db_name]
    
    print("--- Transactions ---")
    count = await db.transactions.count_documents({})
    print(f"Total count: {count}")
    
    async for doc in db.transactions.find().limit(5):
        print(doc)

if __name__ == "__main__":
    asyncio.run(check_transactions())
