# FIX for routers/auth.py in bikezone-backend
#
# Your traceback showed this crash:
#   File "routers\auth.py", line 59, in login
#     print(f"Login attempt for email: {email},Login attempt password {user['password']}")
#   TypeError: 'NoneType' object is not subscriptable
#
# That happens because there's a leftover debug print() that tries to read
# user['password'] BEFORE checking whether a user was even found. When login
# is attempted with an email that doesn't exist, `user` is None, and the
# print() line itself crashes with a 500 error instead of returning a clean
# "Invalid email or password" message.
#
# HOW TO FIX:
# Open bikezone-backend/routers/auth.py, find your login() function, and
# DELETE the print(...) line entirely. It should look like this when done:

@router.post("/login")
async def login(payload: LoginRequest):
    email = payload.email.lower()
    user = await users_collection.find_one({"email": email})

    if not user or not verify_password(payload.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = create_token(str(user["_id"]), user.get("role", "user"))
    return {"token": token, "user": serialize_user(user)}

# That's it — no print() statement anywhere in this function. The
# "if not user or not ..." check must run BEFORE anything touches
# user["password"], which this version already does correctly.
