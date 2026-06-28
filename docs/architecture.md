# SmartSupply Architecture

## Overview

SmartSupply is a single-store, multi-user inventory assistant. One business (store) is modeled with multiple users sharing the same product catalog, sales history, and purchase workflows.

## Backend Layers

### Apps

| App | Responsibility |
|-----|----------------|
| `accounts` | Custom User model (email login), JWT auth, business settings, staff management |
| `products` | Product categories and products |
| `suppliers` | Supplier master data and lead times |
| `sales` | Sale recording with atomic stock deduction |
| `inventory` | Aggregated dashboard endpoint |
| `purchasing` | Reorder recommendations and purchase order workflow |
| `analytics` | Dead stock snapshots, supplier performance, seasonal events |
| `notifications` | In-app notification generation and deduplication |
| `reports` | Read-only report builders and CSV/XLSX exports |

### Shared Code

- `common/models.py` — `TimeStampedModel`, `AuditedModel`
- `common/permissions.py` — `IsOwner`, `IsOwnerOrStaff`, `IsOwnerOrReadOnly`
- `common/test_utils.py` — Test fixtures and authenticated API client helpers

### Settings

| Module | Purpose |
|--------|---------|
| `config.settings.base` | Shared configuration |
| `config.settings.development` | SQLite, DEBUG=True, relaxed security |
| `config.settings.production` | PostgreSQL required, security headers, logging |

## Data Flow

### Sales

```
POST /api/sales/ → Sale.record_sale()
  → select_for_update(product)
  → validate stock
  → create Sale
  → decrement current_stock
  → check_stock_notifications()
```

### Purchase Orders

```
Approve recommendation → Draft PO + line item
PATCH status → ordered  → set ordered_at, expected_delivery_date
PATCH status → received → apply stock, set actual_delivery_date
```

### Recommendations

```
generate_recommendations()
  → ADS (30-day average daily sales)
  → seasonal multiplier
  → ROP = ADS × lead_time + safety_stock (ADS × 3)
  → create/update pending recommendation
```

### Analytics (Nightly)

```
run_nightly_analytics
  → update dead stock snapshots
  → update supplier performance snapshots
  → generate dead stock / supplier delay notifications
```

## Frontend Structure

```
src/
├── api/           # Axios client + endpoint wrappers
├── components/    # Layout, UI, report components
├── context/       # AuthContext (JWT)
├── pages/         # Route pages
├── routes/        # React Router config
└── utils/         # Safe localStorage helpers
```

## Security Model

- JWT bearer tokens for API authentication
- Role checks on backend views (never rely on frontend alone)
- Stock integrity enforced at serializer level
- Production settings require explicit `SECRET_KEY` and PostgreSQL credentials

## Intentional Constraints

- No public user registration
- No automatic purchasing
- No ML / external forecasting APIs
- Stock not editable via product CRUD
