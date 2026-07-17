import base64

from fastapi import APIRouter, HTTPException, Response

from database import db

router = APIRouter(prefix="/api/assets", tags=["assets"])

assets_collection = db["assets"]


@router.get("/{name}")
async def get_asset(name: str):
    """
    Serves a binary asset (logo, favicon, etc.) stored in MongoDB.
    Documents look like: { "_id": "logo", "content_type": "image/png", "data": "<base64>" }
    """
    asset = await assets_collection.find_one({"_id": name})
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset '{name}' not found.")

    raw_bytes = base64.b64decode(asset["data"])
    return Response(
        content=raw_bytes,
        media_type=asset.get("content_type", "application/octet-stream"),
        headers={"Cache-Control": "public, max-age=3600"},
    )
