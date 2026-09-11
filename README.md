# SmartSupply

Smart inventory assistant for small-to-medium retail businesses. SmartSupply analyzes sales history, supplier performance, seasonal events, and stock levels to provide recommendations — the owner always has final control.

**Core principle:** Assistant, not autopilot. Recommendations require owner approval; the system never auto-purchases.

## Tech Stack

| Layer | Technologies |
|-------|--------------|
| Frontend | React 18, Vite, React Router, Tailwind CSS, Axios, Recharts |
| Backend | Django 5, Django REST Framework, PostgreSQL (production), SQLite (development) |
| Auth | JWT (djangorestframework-simplejwt) |

## Features

- **Authentication & roles** — Owner and Staff; owner creates staff accounts
- **Inventory** — Products, categories, suppliers, sales recording
- **Recommendations** — Reorder point engine with seasonal multipliers
- **Purchase orders** — Draft → Ordered → Received workflow
- **Analytics** — Dead stock, supplier performance, seasonal events
- **Notifications** — Low stock, out of stock, dead stock, supplier delays, recommendations
- **Reports** — Inventory, sales, dead stock, suppliers, recommendations with CSV/Excel export

## Architecture

```
smartsupply/
├── backend/                 # Django REST API
│   ├── apps/
│   │   ├── accounts/        # Users, settings, JWT auth
│   │   ├── products/        # Products & categories
│   │   ├── suppliers/       # Suppliers
│   │   ├── sales/           # Sales & stock reduction
│   │   ├── inventory/       # Dashboard API
│   │   ├── purchasing/      # Recommendations & POs
│   │   ├── analytics/       # BI snapshots & seasonal events
│   │   ├── notifications/   # In-app alerts
│   │   └── reports/         # Reports & exports
│   ├── common/              # Shared models & permissions
│   └── config/              # Settings (development / production)
├── frontend/                # React SPA
└── docs/                    # Extended documentation
```

See [docs/architecture.md](docs/architecture.md) for details.

## Installation

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker (optional, for PostgreSQL)

### Environment Setup

**Backend** — copy and edit environment file:

```bash
cd backend
cp .env.example .env
```

**Frontend**:

```bash
cd frontend
cp .env.example .env
```

### Database Setup

**Option A — SQLite (quick local dev):**

Uses `config.settings.development` automatically via `manage.py`. No Docker required.

**Option B — PostgreSQL:**

```bash
docker compose up -d
```

Set `DJANGO_SETTINGS_MODULE=config.settings.base` or configure PostgreSQL in `development.py`.

### Running Backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
python manage.py migrate
python manage.py create_owner --email owner@store.com --password changeme123 --name "Store Owner" --store "My Store"
python manage.py runserver
```

API: `http://localhost:8000`

### Running Frontend

```bash
cd frontend
npm install
npm run dev
```

App: `http://localhost:5173`

### Running Tests

```bash
cd backend
.venv\Scripts\activate   # or source .venv/bin/activate
python manage.py test
```

### Generating Reports

1. Log in as Owner or Staff
2. Navigate to **Reports** in the sidebar
3. Open any report, select a date range, and use **Export CSV** or **Export Excel**

Export URLs use `export_format=csv|xlsx` (not `format`, which conflicts with DRF content negotiation).

### Nightly Analytics

Run manually or via cron:

```bash
python manage.py run_nightly_analytics
```

Or trigger from the UI (owner): **Supplier Analytics** → Run Analytics, or `POST /api/analytics/run/`.

This refreshes supplier snapshots, dead stock, **ARIMA demand forecasts**, and reorder recommendations.

## Demand Forecasting (ARIMA)

See [docs/forecasting.md](docs/forecasting.md).

- UI: **Demand Forecast** in the sidebar
- API: `GET /api/analytics/forecast/`
- Report: **Reports → Demand Forecast Report** (CSV/Excel)

Forecasts advise only — they never place orders or approve recommendations.

## Default User Roles

| Role | Access |
|------|--------|
| **Owner** | Full access: settings, staff, categories, suppliers, recommendations approval, PO status changes |
| **Staff** | Read/write inventory operations, view analytics, reports, notifications; cannot manage settings or approve recommendations |

## Default Login

After `create_owner`:

- **Email:** owner@store.com
- **Password:** changeme123

## Production Deployment

Set `DJANGO_SETTINGS_MODULE=config.settings.production` and configure variables from `.env.production.example`. See [docs/deployment.md](docs/deployment.md).

WSGI/ASGI default to production settings; `manage.py` defaults to development for local use.

## Documentation

- [Architecture](docs/architecture.md)
- [API Overview](docs/api-overview.md)
- [Deployment](docs/deployment.md)
- [Demand Forecasting (ARIMA)](docs/forecasting.md)

## Stock Integrity

Stock levels cannot be edited via the Product API. Changes occur only through:

- **Sales** — reduces stock
- **Purchase order receipt** — increases stock

Inventory adjustments (manual corrections) are planned for a future release.
