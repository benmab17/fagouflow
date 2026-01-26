# FagouFlow (API + Admin)

Prototype Django 5.x + DRF, PostgreSQL, Redis, JWT auth.

## Prerequisites
- Docker + Docker Compose

## Quick start

```bash
docker compose up -d --build
docker compose exec web python manage.py migrate
docker compose exec web python manage.py seed_demo
docker compose exec web python manage.py createsuperuser
docker compose exec web pytest
```

API available at http://localhost:8000
Admin at http://localhost:8000/admin

## JWT Auth

Obtain token:

```bash
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"email":"boss@fagouflow.local","password":"password"}'
```

Refresh token:

```bash
curl -X POST http://localhost:8000/api/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh":"<refresh_token>"}'
```

## Reports

Boss/HQ endpoints:
- `GET /api/reports/audit/daily?date=YYYY-MM-DD`
- `GET /api/reports/audit/weekly?year=YYYY&week=WW`
- `GET /api/reports/audit/monthly?year=YYYY&month=MM`

Generate report file:

```bash
docker compose exec web python manage.py generate_audit_report --period daily --date 2026-01-24
```

JSON files are written to `/app/reports_out` (mounted to `./reports_out`).