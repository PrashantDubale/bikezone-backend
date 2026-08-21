"""
One-time (or repeatable) script to load your bike JSON file into MongoDB.
Run from the bikezone-backend folder:

    python seed_bikes.py

Safe to re-run — it clears the bikes collection first, so you won't get
duplicates.
"""

import asyncio
import json
import re
from pathlib import Path

from database import bikes_collection

# Resolved relative to this script's own folder, so it works no matter
# which directory you run "python seed_bikes.py" from, and on any machine
# (the old hardcoded "d:\PD\..." path only existed on one dev's laptop).
DATA_FILE = Path(__file__).resolve().parent / "data" / "bikes-source.json"
IMAGE_FALLBACK = "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=500&h=400&fit=crop"


def parse_price(value) -> int:
    if isinstance(value, (int, float)):
        return int(value)
    if not value:
        return 0
    text = str(value).replace(",", "").strip()
    if " - " in text:
        text = text.split(" - ", 1)[0]
    numbers = [int(n) for n in re.findall(r"\d+", text)]
    return numbers[0] if numbers else 0


def resolve_image_value(raw_bike) -> str:
    image_value = raw_bike.get("image") or raw_bike.get("images") or raw_bike.get("image_url")

    if isinstance(image_value, str):
        image_value = image_value.strip()
        return image_value or IMAGE_FALLBACK

    if isinstance(image_value, list):
        for item in image_value:
            if isinstance(item, str) and item.strip():
                return item.strip()
            if isinstance(item, dict):
                for key in ("url", "src", "href", "image"):
                    value = item.get(key)
                    if isinstance(value, str) and value.strip():
                        return value.strip()

    if isinstance(image_value, dict):
        for key in ("url", "src", "href", "image"):
            value = image_value.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

    return IMAGE_FALLBACK


def slugify(brand: str, name: str) -> str:
    text = f"{brand}-{name}".lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def normalize_bike(raw_bike, index: int) -> dict:
    price = parse_price(raw_bike.get("price_inr", raw_bike.get("price", 0)))
    engine_cc = raw_bike.get("engine_cc", 0)
    horsepower = raw_bike.get("max_power_hp", raw_bike.get("horsepower", 0))
    torque = raw_bike.get("max_torque_nm", raw_bike.get("torque", 0))
    mileage = raw_bike.get("mileage_kmpl", raw_bike.get("mileage", 0))
    top_speed = raw_bike.get("top_speed_kmph", raw_bike.get("top_speed", 0))
    fuel_tank = raw_bike.get("fuel_tank_liters", raw_bike.get("fuel_tank", 0))
    kerb_weight = raw_bike.get("kerb_weight_kg", raw_bike.get("kerb_weight", 0))
    seat_height = raw_bike.get("seat_height_mm", raw_bike.get("seat_height", 0))
    ground_clearance = raw_bike.get("ground_clearance_mm", raw_bike.get("ground_clearance", 0))
    wheelbase = raw_bike.get("wheelbase_mm", raw_bike.get("wheelbase", 0))
    image_url = resolve_image_value(raw_bike)
    brand = raw_bike.get("brand", "")
    name = raw_bike.get("model") or raw_bike.get("name", "")

    return {
        "id": slugify(brand, name) or str(index + 1),
        "name": name,
        "brand": brand,
        "category": raw_bike.get("category", ""),
        "launch_year": raw_bike.get("launch_year", ""),
        "price": price,
        "price_range": raw_bike.get("price_range", ""),
        "engine_cc": engine_cc,
        "horsepower": horsepower,
        "power_rpm": raw_bike.get("max_power_rpm", raw_bike.get("power_rpm", "")),
        "torque": torque,
        "torque_rpm": raw_bike.get("max_torque_rpm", raw_bike.get("torque_rpm", "")),
        "cooling_system": raw_bike.get("cooling_system", ""),
        "gearbox": raw_bike.get("gearbox", ""),
        "fuel_tank": fuel_tank,
        "kerb_weight": kerb_weight,
        "seat_height": seat_height,
        "ground_clearance": ground_clearance,
        "wheelbase": wheelbase,
        "front_tyre": raw_bike.get("front_tyre", ""),
        "rear_tyre": raw_bike.get("rear_tyre", ""),
        "abs_type": raw_bike.get("abs_type", ""),
        "top_speed": top_speed,
        "mileage": mileage,
        "fuel_type": raw_bike.get("fuel_type", "Petrol"),
        "image": image_url,
        "images": [image_url],
        "specs": {
            "engine_cc": engine_cc,
            "power": horsepower,
            "torque": torque,
            "mileage": mileage,
            "top_speed": top_speed,
        },
    }


async def seed():
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Could not find bike data at {DATA_FILE}. "
            "Make sure data/bikes-source.json exists next to this script."
        )

    with DATA_FILE.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    motorcycles = payload.get("motorcycles", payload if isinstance(payload, list) else [])
    bikes = [normalize_bike(bike, index) for index, bike in enumerate(motorcycles)]

    print(f"Preparing to import {len(bikes)} bikes...")
    await bikes_collection.delete_many({})
    if bikes:
        await bikes_collection.insert_many(bikes)
    print(f"Done. Inserted {len(bikes)} bikes into MongoDB.")


if __name__ == "__main__":
    asyncio.run(seed())
