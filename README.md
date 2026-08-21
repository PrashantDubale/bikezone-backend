# BikeZone — Backend API

A FastAPI + MongoDB backend for **BikeZone**, a motorcycle marketplace app —
serving bike listings, search/filter/sort, and JWT-based auth with
role-based admin access for managing the catalog.

**Live API:** https://bikezone-backend.onrender.com
**Frontend repo:** https://github.com/PrashantDubale/bikezone-frontend

## Tech stack

- **FastAPI** (Python) — REST API
- **MongoDB** (via Motor, async driver) — data store
- **JWT** (python-jose) — authentication
- **Passlib (bcrypt)** — password hashing
- Deployed on **Render**

## Features

- Public endpoints to browse, search, filter, and sort bikes by brand,
  category, price, and engine displacement
- Bike comparison endpoint
- JWT-based register/login
- Role-based access control — only admins can create, update, or delete
  bike listings; regular users get a 403, not a 401
- Seed script to bulk-load bike data from JSON into MongoDB

## Project structure

```
bikezone-backend/
├── main.py              # FastAPI app entrypoint
├── database.py          # MongoDB connection (Motor)
├── auth_utils.py        # JWT + password hashing helpers
├── routers/
│   ├── auth.py           # /api/auth/register, /api/auth/login
│   └── bikes.py          # /api/bikes, /api/brands, /api/featured, etc.
├── data/
│   └── bikes-source.json # Seed data
├── seed_bikes.py         # One-time script to load bikes into MongoDB
├── make_admin.py         # Promotes an existing user to admin
└── requirements.txt
```

## Running locally

1. **Install dependencies**
   ```
   python -m venv venv
   venv\Scripts\activate        # Windows
   pip install -r requirements.txt
   ```

2. **Set up environment variables** — copy `.env.example` to `.env` and fill
   in your own values:
   ```
   MONGODB_URI=mongodb://localhost:27017/bikezone
   JWT_SECRET=replace-this-with-a-long-random-string
   PORT=8000
   ```
   Never commit your real `.env` file — see `.gitignore`.

3. **Seed the database**
   ```
   python seed_bikes.py
   ```

4. **Run the server**
   ```
   python main.py
   ```
   API will be live at `http://localhost:8000`.

5. **Create an admin account**
   - Register a normal account through `/api/auth/register` (or via the
     frontend's signup page).
   - Promote it:
     ```
     python make_admin.py your@email.com
     ```

## API overview

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/api/bikes` | List all bikes | Public |
| GET | `/api/bikes/{id}` | Bike detail | Public |
| GET | `/api/bikes/search?q=` | Search by name/brand | Public |
| GET | `/api/brands` | List distinct brands | Public |
| GET | `/api/categories` | List distinct categories | Public |
| GET | `/api/featured` | Top bikes by horsepower | Public |
| POST | `/api/bikes/filter` | Filter by brand/category/price/cc | Public |
| POST | `/api/bikes/sort` | Sort by price/power/mileage/etc. | Public |
| POST | `/api/compare` | Compare multiple bikes by id | Public |
| POST | `/api/auth/register` | Create an account | Public |
| POST | `/api/auth/login` | Log in, get a JWT | Public |
| POST | `/api/bikes` | Create a bike | Admin only |
| PUT | `/api/bikes/{id}` | Update a bike | Admin only |
| DELETE | `/api/bikes/{id}` | Delete a bike | Admin only |
