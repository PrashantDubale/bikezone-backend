import os
import certifi
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv


load_dotenv()


MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/bikezone")


client = AsyncIOMotorClient(MONGODB_URI, tlsCAFile=certifi.where())
db = client.get_database(os.getenv("MONGODB_DATABASE", "bikezone"))


bikes_collection = db["bikes"]
users_collection = db["users"]
