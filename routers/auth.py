from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

from auth_utils import create_token, hash_password, verify_password
from database import users_collection

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


def serialize_user(user: dict) -> dict:
    return {
        "id": str(user["_id"]),
        "name": user["name"],
        "email": user["email"],
        "role": user.get("role", "user"),
    }


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest):
    # Always creates a normal "user" — admins are promoted separately
    # via make_admin.py, never through the public signup form.
    if len(payload.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")

    email = payload.email.lower()
    existing = await users_collection.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    user_doc = {
        "name": payload.name,
        "email": email,
        "password": hash_password(payload.password),
        "role": "user",
    }
    result = await users_collection.insert_one(user_doc)
    user_doc["_id"] = result.inserted_id

    token = create_token(str(user_doc["_id"]), user_doc["role"])
    return {"token": token, "user": serialize_user(user_doc)}


@router.post("/login")
async def login(payload: LoginRequest):
    email = payload.email.lower()
    user = await users_collection.find_one({"email": email})

    if not user or not verify_password(payload.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = create_token(str(user["_id"]), user.get("role", "user"))
    return {"token": token, "user": serialize_user(user)}
