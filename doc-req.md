# SmartSupply — Project Documentation & Run Guide

**Document:** `doc-req.md`  
**Purpose:** Project overview, system description, and complete instructions to set up and run SmartSupply end-to-end.

---

## 1. About the Project

**SmartSupply** is a web-based **smart inventory assistant** for small-to-medium single-store retail businesses. It helps store owners and staff manage products, record sales, track suppliers, and make better restocking decisions using sales history, seasonal events, supplier performance, and predictive demand forecasting.

### Core principle

> **Assistant, not autopilot.**

SmartSupply **advises**; the owner **decides**.

The system:

- Generates reorder recommendations
- Shows demand forecasts and analytics
- Sends in-app notifications

The system **never**:

- Automatically places purchase orders
- Automatically approves recommendations
- Automatically changes prices or discounts
- Makes irreversible business decisions without the owner

---

## 2. Problem Statement

Retail stores often struggle with:

| Problem | Business impact |
|---------|-----------------|
| Stockouts | Lost sales |
| Overstock / dead stock | Tied-up capital |
| Manual reorder guessing | Inconsistent purchasing |
| Weak supplier visibility | Unexpected delays |
| Seasonal demand shifts | Wrong quantities ordered |

SmartSupply addresses these by combining inventory operations with advisory analytics in one application.

---

## 3. Objectives

1. Secure role-based access for **Owner** and **Staff**
2. Maintain product, category, supplier, and sales data
3. Calculate reorder points using demand and lead time
4. Support seasonal demand adjustments
5. Provide ARIMA-based demand forecasting when enough history exists
6. Track dead stock and supplier performance
7. Support purchase order workflows with owner control
8. Provide reports with CSV/Excel export
9. Keep the owner in full control of purchasing decisions

---

## 4. Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18, Vite, React Router, Tailwind CSS, Axios, Recharts |
| Backend | Django 5, Django REST Framework |
| Auth | JWT (`djangorestframework-simplejwt`) |
| Database (dev) | SQLite |
| Database (prod) | PostgreSQL |
| Forecasting | ARIMA via `statsmodels` (+ `numpy`, `pandas`) |
| Exports | CSV and Excel (`openpyxl`) |
| Optional infra | Docker Compose (PostgreSQL only) |

---

## 5. System Architecture (High Level)

```
┌─────────────────────┐         JWT + REST          ┌──────────────────────┐
│  React Frontend     │  ◄──────────────────────►   │  Django REST API     │
│  (localhost:5173)   │                             │  (localhost:8000)    │
└─────────────────────┘                             └──────────┬───────────┘
                                                               │
                                                    ┌──────────▼───────────┐
                                                    │  SQLite / PostgreSQL │
                                                    └──────────────────────┘
```

### Project structure

```
smartsupply/
├── backend/                 # Django REST API
│   ├── apps/
│   │   ├── accounts/        # Users, JWT auth, settings, staff
│   │   ├── products/        # Products & categories
│   │   ├── suppliers/       # Suppliers & lead times
│   │   ├── sales/           # Sales & stock reduction
│   │   ├── inventory/       # Dashboard & business advisor
│   │   ├── purchasing/      # Recommendations, POs, Profit Advisor
│   │   ├── analytics/       # Dead stock, seasonal, forecasts (ARIMA)
│   │   ├── notifications/   # In-app alerts
│   │   └── reports/         # Reports & CSV/Excel export
│   ├── common/              # Shared models & permissions
│   ├── config/              # Settings (development / production)
│   ├── manage.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/                # React SPA
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── routes/
│   │   └── context/
│   └── .env.example
├── docs/                    # Extended documentation
├── docker-compose.yml       # Optional PostgreSQL
├── README.md
└── doc-req.md               # This file
```

---

## 6. Main Features

### 6.1 Authentication & roles

| Role | Capabilities |
|------|----------------|
| **Owner** | Full access: settings, staff, categories, suppliers, approve/dismiss recommendations, PO status changes, run analytics, Profit Advisor |
| **Staff** | Day-to-day ops: products (read), sales, view recommendations/POs/analytics/reports/notifications; cannot manage settings or approve recommendations |

- No public self-registration
- Initial owner is created via management command
- Staff accounts are created by the Owner (Staff page)

### 6.2 Inventory operations

- Categories, suppliers, products
- Sales recording (reduces stock atomically)
- Stock is **not** editable via product forms — only sales (down) and PO receipt (up)

### 6.3 Reorder recommendations

- Computes Average Daily Sales (ADS) or ARIMA forecasted demand
- Applies Seasonal Intelligence only on the Historical ADS path
- Calculates Reorder Point (ROP) and recommended quantity
- Assigns Operational Priority (HIGH / MEDIUM / LOW)
- Owner must **Approve** (creates Draft PO) or **Dismiss**

### 6.4 Purchase orders

- Sources: from recommendation approval, or **manual** PO creation
- Status flow: `Draft → Ordered → Received` (or Cancelled)
- Receiving a PO increases stock

### 6.5 Analytics & advisors

| Module | Purpose |
|--------|---------|
| Dead Stock | Flags products with no recent sales |
| Dead Stock Advisor | Suggests discount/bundle/stop-reorder actions |
| Supplier Analytics | Lead time, delay, on-time rate + insights |
| Seasonal Events | Calendar multipliers for categories |
| Demand Forecast (ARIMA) | Predicted daily demand for next 7 days |
| Profit Advisor | Budget-based prioritization of pending recommendations |
| Business Advisor | Factual dashboard messages |

### 6.6 Notifications (in-app only)

Types: Low Stock, Out of Stock, Dead Stock, Supplier Delay, Reorder Recommendation.

- Stored in database
- Shown via navbar bell (polls every ~60 seconds)
- **Not** email/SMS/push

### 6.7 Reports

Inventory, Sales, Dead Stock, Suppliers, Recommendations, Demand Forecast, Profit Advisor — with **CSV** and **Excel** export.

---

## 7. Important Algorithms (Brief)

These are **separate** concepts — do not treat them as one algorithm.

| Concept | What it does |
|---------|----------------|
| **Historical ADS** | 30-day average daily sales from sale history |
| **Seasonal Intelligence** | Multiplies ADS by active seasonal event multipliers (fallback path only) |
| **ARIMA Forecast** | Time-series predicted demand when ≥30 days of history exist |
| **ROP** | `demand × lead_time + demand × 3` (safety stock) |
| **Operational Priority** | Urgency ranking of pending recommendations |
| **Profit Advisor** | Suggests which pending items fit a budget (does not auto-buy) |

### Demand source used for recommendations

```
IF ARIMA forecast available:
    use predicted daily demand
    do NOT re-apply seasonal multiplier
ELSE:
    use Historical ADS × seasonal multiplier
```

Forecasts and recommendations remain **advisory**.

---

## 8. Prerequisites

Install before running:

| Requirement | Version / notes |
|-------------|-----------------|
| Python | 3.11+ |
| Node.js | 18+ |
| npm | Comes with Node.js |
| Docker | Optional — only if using PostgreSQL via Compose |

---

## 9. How to Run the Project Fully (Local Development)

Commands below use **Windows PowerShell** paths. On macOS/Linux, use `source .venv/bin/activate` instead of `.venv\Scripts\activate`, and `cp` instead of `copy`.

### Step 1 — Backend environment file

```powershell
cd C:\Users\sales\smartsupply\backend
copy .env.example .env
```

### Step 2 — Create virtual environment and install dependencies

```powershell
cd C:\Users\sales\smartsupply\backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

This installs Django, DRF, JWT, Excel export, and ARIMA libraries (`numpy`, `pandas`, `statsmodels`).

### Step 3 — Database migrations

**Default (recommended for local work): SQLite** — no Docker required.

```powershell
python manage.py migrate
```

**Optional PostgreSQL:**

```powershell
cd C:\Users\sales\smartsupply
docker compose up -d
```

Then configure DB settings in `backend/.env` and run `migrate` again.

### Step 4 — Create the store Owner (required once)

```powershell
cd C:\Users\sales\smartsupply\backend
.venv\Scripts\activate
python manage.py create_owner --email owner@store.com --password changeme123 --name "Store Owner" --store "My Store"
```

### Step 5 — (Optional) Seed demo inventory

```powershell
python manage.py seed_inventory
```

Other optional demo commands:

```powershell
python manage.py seed_dead_stock_demo
python manage.py generate_demo_recommendations
python manage.py run_nightly_analytics
```

### Step 6 — Start the backend server

```powershell
cd C:\Users\sales\smartsupply\backend
.venv\Scripts\activate
python manage.py runserver
```

- API base: **http://localhost:8000**
- Health (if enabled): **http://localhost:8000/api/health/** or project health route

Leave this terminal running.

### Step 7 — Frontend environment and install

Open a **second** terminal:

```powershell
cd C:\Users\sales\smartsupply\frontend
copy .env.example .env
npm install
```

Frontend `.env` uses:

```
VITE_API_BASE_URL=/api
```

Vite proxies `/api` to `http://localhost:8000` during development.

### Step 8 — Start the frontend

```powershell
cd C:\Users\sales\smartsupply\frontend
npm run dev
```

- App URL: **http://localhost:5173**

### Step 9 — Log in

Open **http://localhost:5173** and sign in with:

| Field | Value |
|-------|--------|
| Email | `owner@store.com` |
| Password | `changeme123` |

Change the password after first login via **Change password** in the navbar if desired.

---

## 10. Creating Staff Users

### In the app (recommended)

1. Log in as **Owner**
2. Open **Staff** in the sidebar
3. Create staff with email, full name, and password (minimum 8 characters)

### Notes

- There is no separate “Admin” app role — **Owner** is the store administrator
- Django `createsuperuser` is only for `/admin/` (optional), not for the SmartSupply UI

```powershell
cd C:\Users\sales\smartsupply\backend
.venv\Scripts\activate
python manage.py createsuperuser
```

Then visit **http://localhost:8000/admin/**

---

## 11. Typical Daily Usage Flow

1. **Staff/Owner** records sales on **Sales**
2. Owner runs analytics / generates recommendations (or nightly job)
3. Review **Recommendations** (Demand column shows ARIMA or Historical ADS)
4. Owner approves selected items → Draft POs created
5. Move POs to **Ordered**, then **Received** when goods arrive
6. Check **Dead Stock**, **Demand Forecast**, **Supplier Analytics**
7. Export reports from **Reports** as needed

---

## 12. Useful Management Commands

| Command | Purpose |
|---------|---------|
| `python manage.py migrate` | Apply database migrations |
| `python manage.py create_owner ...` | Create first owner + store settings |
| `python manage.py runserver` | Start API server |
| `python manage.py seed_inventory` | Sample products/suppliers/categories |
| `python manage.py generate_demo_recommendations` | Generate reorder recommendations |
| `python manage.py run_nightly_analytics` | Supplier snapshots + dead stock + forecasts + recommendations |
| `python manage.py seed_dead_stock_demo` | Demo dead-stock scenarios |
| `python manage.py test` | Run backend automated tests |
| `python manage.py createsuperuser` | Django admin user (optional) |

---

## 13. Frontend Scripts

```powershell
cd C:\Users\sales\smartsupply\frontend
npm run dev       # development server
npm run build     # production build
npm run preview   # preview production build
```

---

## 14. Quick Start Checklist

- [ ] Python 3.11+ and Node.js 18+ installed
- [ ] Backend `.env` created from `.env.example`
- [ ] Virtualenv created; `pip install -r requirements.txt`
- [ ] `python manage.py migrate`
- [ ] `python manage.py create_owner ...`
- [ ] `python manage.py runserver` running on port 8000
- [ ] Frontend `.env` created; `npm install`
- [ ] `npm run dev` running on port 5173
- [ ] Login works with owner credentials
- [ ] (Optional) Seed inventory and run nightly analytics

---

## 15. Stock Integrity Rules

Stock changes **only** through:

1. **Sales** — decrease stock  
2. **Purchase order received** — increase stock  

Product create/edit does **not** allow arbitrary stock edits.

---

## 16. Related Documentation

| Document | Contents |
|----------|----------|
| [README.md](README.md) | Short project intro and install summary |
| [docs/architecture.md](docs/architecture.md) | Architecture and data flows |
| [docs/api-overview.md](docs/api-overview.md) | REST API endpoints |
| [docs/forecasting.md](docs/forecasting.md) | ARIMA forecasting design |
| [docs/deployment.md](docs/deployment.md) | Production deployment notes |

---

## 17. Summary

SmartSupply is a **decision-support inventory system** for one store with Owner/Staff roles. It combines operational workflows (products, sales, POs) with advisory engines (ROP recommendations, seasonal multipliers, ARIMA forecasts, dead stock, supplier insights, profit advisor, reports, and notifications) while preserving owner control over every purchasing decision.

To run locally: start the **Django API** on port **8000** and the **React app** on port **5173**, then log in with the owner account created by `create_owner`.
