import os
from dotenv import load_dotenv

# Try to find .env in various locations
dotenv_paths = [
    ".env",
    "backend/.env",
    "../.env",
    "d:/PropertyAI/backend/.env"
]

for path in dotenv_paths:
    if os.path.exists(path):
        print(f"Found .env at: {path}")
        load_dotenv(path)

print(f"MONGO_URI: {os.getenv('MONGO_URI')}")
print(f"DB_NAME: {os.getenv('DB_NAME')}")
print(f"GEMINI_API_KEY: {os.getenv('GEMINI_API_KEY')[:10]}...")
print(f"GEOCODE_API_KEY: {os.getenv('GEOCODE_API_KEY')[:10]}...")
print(f"MAPS_API_KEY: {os.getenv('MAPS_API_KEY')[:10]}...")
