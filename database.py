import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/bikezone")

client = AsyncIOMotorClient(MONGODB_URI)
db = client.get_default_database()

bikes_collection = db["bikes"]
users_collection = db["users"]
