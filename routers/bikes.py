import re
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from pymongo import ReturnDocument

from auth_utils import require_admin
from database import bikes_collection

router = APIRouter(prefix="/api", tags=["bikes"])


class BikeIn(BaseModel):
    id: Optional[str] = None
    brand: str
    name: str
    category: Optional[str] = ""
    launch_year: Optional[int] = None
    engine_cc: Optional[int] = None
    horsepower: Optional[float] = None
    torque: Optional[float] = None
    top_speed: Optional[int] = None
    mileage: Optional[float] = None
    gearbox: Optional[str] = ""
    cooling_system: Optional[str] = ""
    fuel_tank: Optional[float] = None
    price: int
    price_range: Optional[str] = ""
    images: Optional[List[str]] = []
    image: Optional[str] = ""
    is_new: Optional[bool] = False
    is_featured: Optional[bool] = False


def slugify(brand: str, name: str) -> str:
    text = f"{brand}-{name}".lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def build_specs(data: dict) -> dict:
    return {
        "engine_cc": data.get("engine_cc"),
        "power": data.get("horsepower"),
        "torque": data.get("torque"),
        "mileage": data.get("mileage"),
        "top_speed": data.get("top_speed"),
    }


def serialize_bike(bike: dict) -> dict:
    bike["_id"] = str(bike["_id"])
    bike.setdefault("is_new", False)
    bike.setdefault("is_featured", False)
    return bike


async def enforce_single_featured(bike_id: str, is_featured: bool):
    """
    Only one bike can be the homepage-pinned featured bike at a time.
    When a bike is marked featured, unmark every other bike.
    """
    if is_featured:
        await bikes_collection.update_many(
            {"id": {"$ne": bike_id}}, {"$set": {"is_featured": False}}
        )


# ---------- Public routes: anyone (logged in or not) can view bikes ----------

@router.get("/bikes")
async def get_bikes(skip: int = 0, limit: int = 200):
    cursor = bikes_collection.find().skip(skip).limit(limit)
    return [serialize_bike(b) async for b in cursor]


@router.get("/bikes/search")
async def search_bikes(q: str = ""):
    if not q:
        cursor = bikes_collection.find()
    else:
        regex = {"$regex": re.escape(q), "$options": "i"}
        cursor = bikes_collection.find({"$or": [{"name": regex}, {"brand": regex}]})
    return [serialize_bike(b) async for b in cursor]


@router.get("/brands")
async def get_brands():
    brands = await bikes_collection.distinct("brand")
    return sorted([b for b in brands if b])


@router.get("/categories")
async def get_categories():
    categories = await bikes_collection.distinct("category")
    return sorted([c for c in categories if c])


@router.get("/featured")
async def get_featured():
    """
    Returns up to 6 bikes for the featured grid, sorted by horsepower.
    If an admin has pinned a specific bike as the homepage feature
    (is_featured: true), that bike is placed first in the list so
    Home.vue's heroFeaturedBike (which reads featured[0]) shows it.
    """
    pinned = await bikes_collection.find_one({"is_featured": True})

    cursor = bikes_collection.find().sort("horsepower", -1).limit(6)
    top_bikes = [serialize_bike(b) async for b in cursor]

    if pinned:
        pinned = serialize_bike(pinned)
        # remove it from the list if it's already in there, then put it first
        top_bikes = [b for b in top_bikes if b["id"] != pinned["id"]]
        top_bikes = [pinned] + top_bikes

    return top_bikes[:6]


@router.get("/health")
async def health_check():
    count = await bikes_collection.count_documents({})
    return {"status": "ok", "bikes_count": count}


@router.post("/bikes/filter")
async def filter_bikes(
    brand: Optional[str] = None,
    category: Optional[str] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    min_cc: Optional[int] = None,
    max_cc: Optional[int] = None,
):
    query: dict = {}
    if brand:
        query["brand"] = {"$regex": f"^{re.escape(brand)}$", "$options": "i"}
    if category:
        query["category"] = {"$regex": f"^{re.escape(category)}$", "$options": "i"}
    if min_price is not None or max_price is not None:
        query["price"] = {}
        if min_price is not None:
            query["price"]["$gte"] = min_price
        if max_price is not None:
            query["price"]["$lte"] = max_price
    if min_cc is not None or max_cc is not None:
        query["engine_cc"] = {}
        if min_cc is not None:
            query["engine_cc"]["$gte"] = min_cc
        if max_cc is not None:
            query["engine_cc"]["$lte"] = max_cc

    cursor = bikes_collection.find(query)
    return [serialize_bike(b) async for b in cursor]


@router.post("/bikes/sort")
async def sort_bikes(sort_by: str = "price", order: str = "asc"):
    valid_sorts = ["price", "horsepower", "mileage", "top_speed", "engine_cc", "torque"]
    if sort_by not in valid_sorts:
        raise HTTPException(status_code=400, detail=f"Invalid sort field. Valid options: {valid_sorts}")

    direction = -1 if order.lower() == "desc" else 1
    cursor = bikes_collection.find().sort(sort_by, direction)
    return [serialize_bike(b) async for b in cursor]


@router.post("/compare")
async def compare_bikes(bike_ids: List[str]):
    cursor = bikes_collection.find({"id": {"$in": bike_ids}})
    return [serialize_bike(b) async for b in cursor]


@router.get("/bikes/{bike_id}")
async def get_bike(bike_id: str):
    bike = await bikes_collection.find_one({"id": bike_id})
    if not bike:
        raise HTTPException(status_code=404, detail="Bike not found.")
    return serialize_bike(bike)


# ---------- Admin-only routes: create, update, delete ----------
# require_admin checks the JWT is valid AND role == "admin".
# A normal logged-in user hitting these gets a 403, not a 401.

@router.post("/bikes", status_code=201)
async def create_bike(payload: BikeIn, admin: dict = Depends(require_admin)):
    data = payload.dict()

    if not data.get("id"):
        data["id"] = slugify(data["brand"], data["name"])

    existing = await bikes_collection.find_one({"id": data["id"]})
    if existing:
        raise HTTPException(status_code=409, detail="A bike with this id already exists.")

    if data.get("images") and not data.get("image"):
        data["image"] = data["images"][0]

    data["specs"] = build_specs(data)

    result = await bikes_collection.insert_one(data)
    data["_id"] = str(result.inserted_id)

    await enforce_single_featured(data["id"], data.get("is_featured", False))

    return data


@router.put("/bikes/{bike_id}")
async def update_bike(bike_id: str, payload: BikeIn, admin: dict = Depends(require_admin)):
    existing = await bikes_collection.find_one({"id": bike_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Bike not found.")

    data = payload.dict(exclude_unset=True)
    data.pop("id", None)

    if data.get("images") and not data.get("image"):
        data["image"] = data["images"][0]

    merged = {**existing, **data}
    data["specs"] = build_specs(merged)

    updated = await bikes_collection.find_one_and_update(
        {"id": bike_id}, {"$set": data}, return_document=ReturnDocument.AFTER
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Bike not found.")

    if "is_featured" in data:
        await enforce_single_featured(bike_id, data["is_featured"])

    return serialize_bike(updated)


@router.delete("/bikes/{bike_id}")
async def delete_bike(bike_id: str, admin: dict = Depends(require_admin)):
    deleted = await bikes_collection.find_one_and_delete({"id": bike_id})
    if not deleted:
        raise HTTPException(status_code=404, detail="Bike not found.")
    return {"message": "Bike deleted."}