# API Overview

Base URL: `/api/`

All authenticated endpoints require `Authorization: Bearer <access_token>` unless noted.

## Authentication

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| POST | `/auth/login/` | Public | JWT login |
| POST | `/auth/refresh/` | Public | Refresh access token |
| GET | `/auth/me/` | Authenticated | Current user |
| POST | `/auth/change-password/` | Authenticated | Change password |

## Settings & Staff

| Method | Endpoint | Access |
|--------|----------|--------|
| GET/PATCH | `/settings/` | All / Owner (write) |
| GET/POST | `/staff/` | Owner |
| GET/PATCH | `/staff/:id/` | Owner |

## Inventory

| Method | Endpoint | Access |
|--------|----------|--------|
| GET/POST | `/categories/` | Owner / All |
| GET/PATCH | `/categories/:id/` | Owner |
| GET/POST | `/suppliers/` | Owner / All |
| GET/PATCH | `/suppliers/:id/` | Owner |
| GET/POST | `/products/` | All / Owner (write) |
| GET/PATCH | `/products/:id/` | All / Owner (write) |
| GET/POST | `/sales/` | All |
| GET | `/dashboard/` | Authenticated |

**Note:** `current_stock` is read-only on product endpoints.

## Purchasing

| Method | Endpoint | Access |
|--------|----------|--------|
| GET | `/recommendations/` | All / Owner (write actions) |
| POST | `/recommendations/generate/` | Owner |
| POST | `/recommendations/:id/approve/` | Owner |
| POST | `/recommendations/:id/dismiss/` | Owner |
| GET | `/purchase-orders/` | All |
| GET | `/purchase-orders/:id/` | All |
| PATCH | `/purchase-orders/:id/status/` | Owner |

## Analytics

| Method | Endpoint | Access |
|--------|----------|--------|
| GET/POST | `/seasonal-events/` | Owner / All |
| GET/PATCH/DELETE | `/seasonal-events/:id/` | Owner |
| GET | `/dead-stock/` | All |
| GET | `/supplier-analytics/` | All |
| POST | `/analytics/run/` | Owner |
| GET | `/analytics/forecast/` | Owner, Staff |
| POST | `/analytics/forecast/refresh/` | Owner |

## Notifications

| Method | Endpoint | Access |
|--------|----------|--------|
| GET | `/notifications/` | All |
| GET | `/notifications/unread-count/` | All |
| POST | `/notifications/:id/read/` | All |
| POST | `/notifications/mark-all-read/` | All |

## Reports

| Method | Endpoint | Access |
|--------|----------|--------|
| GET | `/reports/` | Owner, Staff |
| GET | `/reports/inventory/` | Owner, Staff |
| GET | `/reports/sales/` | Owner, Staff |
| GET | `/reports/dead-stock/` | Owner, Staff |
| GET | `/reports/suppliers/` | Owner, Staff |
| GET | `/reports/recommendations/` | Owner, Staff |
| GET | `/reports/demand-forecast/` | Owner, Staff |
| GET | `/reports/*/export/?export_format=csv|xlsx` | Owner, Staff |

### Report Query Parameters

- Preset range: `?range=7d|30d|90d`
- Custom range: `?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`

### Export

```
GET /reports/{report}/export/?export_format=csv
GET /reports/{report}/export/?export_format=xlsx
```

Use `export_format` (not `format`) to avoid DRF content negotiation conflicts.

## Health

| Method | Endpoint | Access |
|--------|----------|--------|
| GET | `/health/` | Public |

## Error Responses

Validation errors return HTTP 400 with field-level detail:

```json
{
  "current_stock": ["Stock levels cannot be edited directly..."]
}
```

Report date errors:

```json
{
  "date_range": "Invalid date format. Use YYYY-MM-DD."
}
```

## Pagination

List endpoints paginate at 25 items by default. Response shape:

```json
{
  "count": 100,
  "next": "...",
  "previous": null,
  "results": []
}
```
