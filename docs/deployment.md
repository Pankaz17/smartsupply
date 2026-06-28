# Deployment Guide

This document describes production configuration. SmartSupply does not include Docker images or CI/CD pipelines — configure those for your environment.

## Environment Variables

Copy `backend/.env.production.example` to `.env` and set all values:

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | Long random string (no default in production) |
| `DEBUG` | No | Must be `False` (default) |
| `ALLOWED_HOSTS` | Yes | Comma-separated hostnames |
| `DB_NAME` | Yes | PostgreSQL database name |
| `DB_USER` | Yes | PostgreSQL user |
| `DB_PASSWORD` | Yes | PostgreSQL password |
| `DB_HOST` | Yes | Database host |
| `DB_PORT` | No | Default `5432` |
| `CORS_ALLOWED_ORIGINS` | Yes | Frontend origin(s) |
| `SECURE_SSL_REDIRECT` | No | Default `True` |
| `LOG_LEVEL` | No | Default `INFO` |

## Django Settings

```bash
export DJANGO_SETTINGS_MODULE=config.settings.production
```

- `manage.py` defaults to **development** for local work
- `wsgi.py` / `asgi.py` default to **production** for WSGI servers

## Database

1. Provision PostgreSQL
2. Run migrations: `python manage.py migrate`
3. Create owner: `python manage.py create_owner ...`

## Static Files

```bash
python manage.py collectstatic
```

Serve static files via your reverse proxy or a static file handler (e.g. WhiteNoise — not included by default).

## WSGI Server

Install a production server (not in requirements.txt):

```bash
pip install gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

## Frontend

Build the SPA:

```bash
cd frontend
cp .env.example .env.production
# Set VITE_API_BASE_URL=https://api.yourdomain.com/api
npm run build
```

Serve `frontend/dist/` via nginx or your CDN. Configure the reverse proxy to forward `/api` to Django.

## Nightly Analytics

Schedule via cron or your orchestrator:

```bash
0 2 * * * cd /path/to/backend && DJANGO_SETTINGS_MODULE=config.settings.production /path/to/venv/bin/python manage.py run_nightly_analytics
```

## Security Checklist

- [ ] `SECRET_KEY` is unique and secret
- [ ] `DEBUG=False`
- [ ] `ALLOWED_HOSTS` configured
- [ ] HTTPS enabled (`SECURE_SSL_REDIRECT=True`)
- [ ] PostgreSQL credentials are strong
- [ ] CORS origins restricted to your frontend
- [ ] Django admin password is strong or admin URL restricted

## Health Check

Use `GET /api/health/` for load balancer probes. Consider extending it to verify database connectivity in your deployment layer.
