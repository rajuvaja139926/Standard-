# HOTELBOOK

HOTELBOOK is a full-stack hotel booking demonstration built for an MCA project. It includes a React interface, FastAPI service, MongoDB persistence, seeded hotels, authentication, availability-aware bookings, demo payment, and receipt download.

## Run in this workspace
The frontend is already configured to use `REACT_APP_BACKEND_URL`; the backend uses `MONGO_URL` and `DB_NAME` from `backend/.env`. Start the supervised services and open the frontend preview.

## Demo account
Admin: `admin@hotelbook.com` / `Hotelbook@123`

## Core API
Swagger documentation is available at `/api-docs`. Main routes include `/api/auth`, `/api/hotels`, `/api/bookings`, `/api/reviews`, and `/api/admin/dashboard`.

## Notes
Demo payment is intentionally used when real payment credentials are not configured. No card or payment secret is stored. The packaged source excludes `.env` files and dependencies.