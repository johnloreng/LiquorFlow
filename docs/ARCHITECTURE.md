# LiquorFlow — System Architecture

## 1. Architecture Overview

LiquorFlow is a role-based order and delivery management system for small liquor retailers.

The production deployment separates the application into three primary layers:

```text
┌──────────────────────────────────────────────┐
│                  USERS                       │
│       Admin · Dispatcher · Rider             │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│              PRESENTATION LAYER              │
│              Render Frontend                 │
│              React + Vite                    │
└──────────────────────┬───────────────────────┘
                       │ HTTPS / Axios
                       ▼
┌──────────────────────────────────────────────┐
│                APPLICATION LAYER             │
│              Render Backend                  │
│              FastAPI                         │
│              SQLAlchemy ORM                  │
│              JWT Authentication              │
│              Role-Based Access Control       │
└──────────────────────┬───────────────────────┘
                       │ PostgreSQL
                       ▼
┌──────────────────────────────────────────────┐
│                   DATA LAYER                 │
│             Supabase PostgreSQL              │
│             Production Database              │
└──────────────────────────────────────────────┘
```

---

## 2. Production Components

### Frontend — Render

Technology:

- React
- Vite
- Axios
- React Router

Responsibilities:

- Authentication UI
- Role-specific dashboards
- Order creation
- Product selection
- Delivery assignment interface
- Rider delivery workflow
- Dashboard synchronization
- API communication

Production URL:

`https://liquorflow-frontend.onrender.com`

### Backend — Render

Technology:

- Python 3.14
- FastAPI
- SQLAlchemy
- Pydantic
- Alembic
- PyJWT
- pwdlib / Argon2
- Uvicorn

Responsibilities:

- Authentication
- Authorization
- User management
- Product management
- Customer management
- Order management
- Delivery management
- Delivery status validation
- Persistence through SQLAlchemy

Production URL:

`https://liquorflow-backend.onrender.com`

API documentation:

`https://liquorflow-backend.onrender.com/docs`

### Database — Supabase

Technology:

- PostgreSQL

Responsibilities:

- Persist users
- Persist customers
- Persist products
- Persist orders
- Persist order items
- Persist deliveries
- Persist delivery status history
- Maintain relational integrity

The production application connects to Supabase PostgreSQL through the backend using the `DATABASE_URL` environment variable.

---

## 3. Request Flow

A typical order and delivery request follows this path:

```text
Browser
  │
  │ HTTPS
  ▼
Render Frontend
  │
  │ Axios + JWT
  ▼
Render FastAPI Backend
  │
  │ SQLAlchemy
  ▼
Supabase PostgreSQL
```

The frontend does not connect directly to PostgreSQL. Database access is performed by the backend.

---

## 4. Authentication Flow

```text
User enters credentials
          │
          ▼
POST /api/auth/login
          │
          ▼
FastAPI validates credentials
          │
          ▼
JWT access token generated
          │
          ▼
Frontend stores access token
          │
          ▼
Axios sends Bearer token
          │
          ▼
Protected API endpoint
          │
          ▼
Role-based authorization
```

Passwords are stored as hashes rather than plaintext passwords.

---

## 5. Role-Based Access

LiquorFlow defines three application roles:

| Role | Primary responsibilities |
|---|---|
| ADMIN | System administration, products, customer orders, deliveries, users |
| DISPATCHER | Order visibility, rider assignment, delivery monitoring |
| RIDER | Assigned deliveries and delivery status updates |

Authorization is enforced by protected backend routes rather than relying only on frontend visibility.

---

## 6. Order Lifecycle

```text
ADMIN
  │
  └── Create Order
          │
          ▼
       PENDING
          │
          ▼
      DISPATCHER
          │
          └── Assign Rider
                  │
                  ▼
                RIDER
                  │
                  ▼
              PICKED_UP
                  │
                  ▼
           OUT_FOR_DELIVERY
                  │
                  ▼
              DELIVERED
                  │
                  ▼
          Proof of Delivery
```

The delivery service validates status transitions so that the workflow progresses sequentially.

---

## 7. Core Data Relationships

```text
User
 │
 ├────────────── creates ──────────────► Order
 │
 └────────────── assigns ──────────────► Delivery
                                            │
Customer ───────── belongs to ────────► Order
                                            │
Order ───────────── contains ─────────► OrderItem
                                            │
Product ───────── referenced by ──────► OrderItem
                                            │
Order ───────────── has ───────────────► Delivery
                                            │
Delivery ───────── assigned to ────────► Rider/User
```

Core database tables:

- `users`
- `customers`
- `products`
- `orders`
- `order_items`
- `deliveries`
- `delivery_status_history`
- `alembic_version`

---

## 8. Database Migration Architecture

The production database was migrated from the original Render PostgreSQL instance to Supabase.

### Migration sequence

```text
Original Render PostgreSQL
          │
          │ Backup
          ▼
liquorflow_render_backup.dump
          │
          │ Restore
          ▼
Supabase PostgreSQL
          │
          │ Verify tables + data
          ▼
Update Render DATABASE_URL
          │
          ▼
Render FastAPI Backend
          │
          ▼
Production Read/Write Test
          │
          ▼
Retire Original Render PostgreSQL
```

The migration was validated using both API reads and real production writes.

The production workflow was tested by:

1. Creating an order.
2. Assigning a rider.
3. Updating the delivery through pickup.
4. Updating the delivery to out-for-delivery.
5. Completing the delivery.
6. Recording proof of delivery.

The original Render database was retired only after these checks succeeded.

---

## 9. Deployment Architecture

### Render Frontend

The React/Vite application is deployed as the production frontend.

### Render Backend

The FastAPI application is deployed as the production API.

The backend runs Alembic migrations as part of deployment and starts Uvicorn.

### Supabase

Supabase hosts the production PostgreSQL database.

The database credentials are supplied through Render environment variables and are not stored in source control.

---

## 10. Configuration and Secrets

Production configuration is environment-based.

Important configuration includes:

```text
DATABASE_URL
SECRET_KEY / authentication secret
production seed configuration
```

Secrets must never be committed to GitHub.

The database credentials were rotated after migration and the backend was redeployed and smoke-tested successfully.

---

## 11. Synchronization

The dashboard uses periodic synchronization to refresh operational data.

```text
Dashboard loads
      │
      ▼
Initial API synchronization
      │
      ▼
Periodic refresh
      │
      ▼
Updated orders / deliveries
      │
      └──────► Manual "Sync Now"
```

The current MVP uses polling rather than WebSockets.

---

## 12. Reliability and Validation

The backend protects the workflow through:

- JWT authentication
- Role-based authorization
- Pydantic input validation
- Duplicate delivery assignment protection
- Sequential delivery status validation
- Database constraints and foreign keys
- Automated backend tests

The current automated backend test suite reports:

```text
71 passed
```

Production read/write and delivery workflow testing was also completed after the Supabase migration.

---

## 13. Architecture Trade-offs

### Render for application hosting

Render provides a straightforward deployment path for the React frontend and FastAPI backend.

### Supabase for PostgreSQL

Supabase separates the production database from the application hosting layer. This also avoids dependence on the retired Render PostgreSQL resource.

### REST + polling for the MVP

REST APIs and periodic synchronization keep the MVP implementation relatively simple. Real-time WebSocket synchronization remains a future improvement.

### Role-based backend authorization

Authorization is enforced at the API layer so users cannot gain access simply by manipulating frontend navigation or UI state.

---

## 14. Future Architecture Extensions

Potential future improvements include:

```text
Current MVP
    │
    ├── WebSocket real-time synchronization
    ├── SMS / WhatsApp notifications
    ├── GPS rider tracking
    ├── Map integration
    ├── Online payments
    ├── Inventory alerts
    └── Analytics / reporting
```

These are intentionally outside the current MVP scope.

---

## 15. Final Production Architecture

```text
                         INTERNET
                             │
                             ▼
                ┌───────────────────────┐
                │    Render Frontend    │
                │    React + Vite       │
                └───────────┬───────────┘
                            │
                         HTTPS
                            │
                            ▼
                ┌───────────────────────┐
                │    Render Backend     │
                │    FastAPI            │
                │    SQLAlchemy         │
                │    JWT + RBAC         │
                └───────────┬───────────┘
                            │
                       PostgreSQL
                            │
                            ▼
                ┌───────────────────────┐
                │   Supabase PostgreSQL │
                │   Production Data     │
                └───────────────────────┘
```

This is the current production architecture for LiquorFlow.
