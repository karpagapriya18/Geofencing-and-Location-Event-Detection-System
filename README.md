# Geofencing & Location Event Detection System

FastAPI + SQLAlchemy backend and React + TypeScript + Material UI + Leaflet frontend for creating geofences and detecting enter, exit, inside, and outside events from device coordinates.

## Features

- Circular and polygon geofence management.
- Lightweight HMAC bearer-token login under distinct `/identity/*` routes.
- Full user/device list, detail, and update APIs.
- Coordinate validation with Pydantic.
- GPS accuracy buffer support.
- Duplicate enter/exit prevention by comparing each device's previous geofence state.
- Multiple geofence evaluation for every location ingest.
- Event history with previous and current state.
- Audit trail and database health endpoints.
- Distinct React operations console with sidebar navigation, dashboard metrics, live map, geofence/device/location/event tables, and location intake forms.
- Interactive OpenStreetMap display for geofences, latest locations, and events.
- MySQL, Alembic, Swagger/OpenAPI, Postman collection, Docker, and unit tests.

## Run With Docker

```bash
docker compose up --build
```

- Backend: http://localhost:8000
- Swagger docs: http://localhost:8000/docs
- Frontend: http://localhost:5173
- MySQL: localhost:3306, database `geofence`, user `geofence`, password `geofence`

## Run Backend Locally

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

For fast local testing without MySQL, leave `GEOFENCE_DATABASE_URL` unset. The app defaults to SQLite.

## Run Frontend Locally

```bash
cd frontend
npm install
npm run dev
```

## API Examples

Create an administrator and token:

```bash
curl -X POST http://localhost:8000/api/v1/identity/signup ^
  -H "Content-Type: application/json" ^
  -d "{\"name\":\"Admin\",\"email\":\"admin@example.com\",\"password\":\"secret123\"}"
```

Create a circular geofence:

```bash
curl -X POST http://localhost:8000/api/v1/geofences ^
  -H "Content-Type: application/json" ^
  -d "{\"name\":\"HQ\",\"boundary_type\":\"circle\",\"center_lat\":12.9716,\"center_lng\":77.5946,\"radius_meters\":500,\"accuracy_buffer_meters\":15}"
```

Ingest a location:

```bash
curl -X POST http://localhost:8000/api/v1/locations ^
  -H "Content-Type: application/json" ^
  -d "{\"device_identifier\":\"device-001\",\"latitude\":12.9716,\"longitude\":77.5946,\"accuracy_meters\":10,\"timestamp\":\"2026-10-01T10:00:00Z\"}"
```

Alternative tracking endpoint:

```bash
curl -X POST http://localhost:8000/api/v1/track-points ^
  -H "Content-Type: application/json" ^
  -d "{\"device_identifier\":\"device-001\",\"latitude\":12.9000,\"longitude\":77.5000,\"accuracy_meters\":10,\"timestamp\":\"2026-10-01T10:05:00Z\"}"
```

## Tests

```bash
cd backend
pytest
```

The tests cover haversine distance, circular boundary buffering, polygon inclusion, polygon boundary buffering, and event state transitions.

## Project Structure

```text
backend/
  app/
    api/          FastAPI routers
    core/         Settings
    db/           SQLAlchemy session
    models/       SQLAlchemy tables
    schemas/      Pydantic contracts
    services/     Geospatial and event detection engine
  alembic/        Database migrations
  tests/          Unit tests
frontend/
  src/
    components/   Leaflet map
    services/     Axios API client
    types/        TypeScript API types
postman/
  geofence-system.postman_collection.json
```

## Notes

- In production, add authentication/authorization for administrator endpoints.
- This implementation intentionally does not mirror the referenced screenshots exactly. It provides similar backend and frontend capability with different endpoint names, navigation labels, visual system, product identity, and page composition.
- For very large fleets, add spatial indexes or a geospatial database extension and evaluate only nearby geofences.
- The current event engine intentionally emits repeat `inside` events when enabled, while suppressing duplicate enter/exit events unless the state actually changes.
