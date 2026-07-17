"""
Run this once (from the bikezone-backend folder, with venv active) to push
the logo and favicon into MongoDB:

    python upload_assets.py

It reads the image files listed below from the same folder as this script
and stores them as base64 documents in the "assets" collection. After
running this, the backend serves them at:

    http://localhost:8000/api/assets/logo
    http://localhost:8000/api/assets/favicon

Re-run this script any time you want to replace the logo/favicon — it
overwrites the existing document with the same _id.
"""

import asyncio
import base64
import mimetypes
import sys
from pathlib import Path

from database import db

assets_collection = db["assets"]

# (asset id used in the URL, filename to read, mongo content_type override)
FILES_TO_UPLOAD = [
    ("logo", "bikezone-logo.png", "image/png"),
    ("favicon", "favicon.ico", "image/x-icon"),
]


async def upload_one(asset_id: str, filename: str, content_type: str):
    path = Path(__file__).parent / filename
    if not path.exists():
        print(f"  SKIPPED '{asset_id}': file not found at {path}")
        return

    data = path.read_bytes()
    encoded = base64.b64encode(data).decode("utf-8")

    await assets_collection.update_one(
        {"_id": asset_id},
        {"$set": {"content_type": content_type, "data": encoded}},
        upsert=True,
    )
    print(f"  OK '{asset_id}' <- {filename} ({len(data)} bytes)")


async def main():
    print("Uploading assets to MongoDB...")
    for asset_id, filename, content_type in FILES_TO_UPLOAD:
        await upload_one(asset_id, filename, content_type)
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
