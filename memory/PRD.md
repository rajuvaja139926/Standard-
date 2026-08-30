# HOTELBOOK PRD

## Original problem statement
Build a complete HOTELBOOK hotel booking system with search, filters, hotel details, rooms, date selection, guest details, backend price calculation, payments, confirmation, receipts, bookings, reviews, and admin management.

## Architecture decisions
- React frontend uses the existing supported build and calls FastAPI through `REACT_APP_BACKEND_URL`.
- FastAPI and Motor use the protected MongoDB environment variables; seeded data makes the first run immediately demonstrable.
- Demo payment is the default safe flow; the receipt endpoint is available for every confirmed booking.

## Personas and requirements
- Guests searching for comfortable stays and booking quickly on mobile or desktop.
- Admins monitoring bookings and hotel inventory.
- Core static requirements: hotel discovery, auth, availability protection, transparent price breakdown, confirmation, receipts.

## Implemented (2026-02-01)
- Seeded ten Indian-city hotels with rooms and imagery.
- Added registration, login/logout, cookie JWT sessions, hotel search/sorting, room details, booking creation with overlap protection, demo payment, receipt download, bookings list, reviews endpoint, and admin summary endpoints.
- Built responsive HOTELBOOK UI with home, collection, detail, auth, checkout, confirmation, bookings, and about views.

## Backlog
- P0: Full admin CRUD screens and Razorpay verification wiring.
- P1: Cloudinary uploads, richer PDF binary generation, booking cancellation UI and review composer.
- P2: Monthly charts, pagination, password reset, contact form, production rate limiting.