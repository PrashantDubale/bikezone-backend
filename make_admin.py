"""
Promotes an existing user to admin. Run from the bikezone-backend folder:

    python make_admin.py someone@example.com
"""

import asyncio
import sys

from database import users_collection


async def make_admin(email: str):
    email = email.lower()
    user = await users_collection.find_one({"email": email})

    if not user:
        print(f'No user found with email "{email}". Register the account first, then run this script.')
        sys.exit(1)

    await users_collection.update_one({"_id": user["_id"]}, {"$set": {"role": "admin"}})
    print(f'"{email}" is now an admin.')


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python make_admin.py <email>")
        sys.exit(1)

    asyncio.run(make_admin(sys.argv[1]))
