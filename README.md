# LiquorFlow

### Order & Delivery Management System for Small Liquor Retailers

LiquorFlow is a web-based order and delivery management system designed to help small liquor retailers move from informal WhatsApp/phone-based delivery coordination to a structured, trackable workflow.

The system connects **administrators, attendants, dispatchers, and riders** through role-based access and provides visibility throughout the delivery lifecycle — from order creation to proof of delivery.

---

## Project Overview

Small retailers often coordinate customer deliveries through phone calls and WhatsApp messages. This can make it difficult to:

- Keep a centralized record of orders
- Know which rider is handling an order
- Track the current delivery status
- Maintain accountability for completed deliveries
- Confirm that a delivery has actually been completed

LiquorFlow addresses these challenges with a centralized digital workflow for managing products, customers, orders, rider assignments, and deliveries.

---

## Solution

LiquorFlow provides a simple role-based workflow:

```text
Create Order
     ↓
   Pending
     ↓
Assign Rider
     ↓
   Assigned
     ↓
  Picked Up
     ↓
Out for Delivery
     ↓
   Delivered
     ↓
Proof of Delivery
```

Each delivery stage is recorded by the system, providing operational visibility and accountability.

---

## User Roles

### Administrator

- Access the management dashboard
- Manage products
- Create customer orders
- Select products and quantities
- View orders
- Oversee deliveries
- Manage system users

### Attendant

- Create customer orders
- Select products and quantities
- View orders
- Support day-to-day order processing

### Dispatcher

- View orders
- View delivery requests
- Assign riders
- Monitor delivery progress

### Rider

- View assigned deliveries
- Update delivery status
- Confirm pickup
- Mark orders as out for delivery
- Complete deliveries
- Provide proof of delivery

---

## Key Features

### Authentication & Authorization

- JWT-based authentication
- Password hashing with Argon2
- Role-based access control
- Protected API endpoints
- Separate workflows for Admin, Attendant, Dispatcher, and Rider

### Product Management

- Create products
- Manage product prices
- Manage stock quantities
- Activate/deactivate products
- Retrieve active products for order creation

### Customer Management

- Create customer records
- Store customer name
- Store customer phone number
- Store delivery address

### Order Management

- Create orders
- Add multiple products to an order
- Specify product quantities
- Automatically calculate order totals
- Track order status
- View orders from the dashboard

### Delivery Management

- Assign riders to orders
- Prevent duplicate delivery assignments
- Track delivery status
- Enforce sequential delivery transitions
- Record delivery timestamps
- Capture proof of delivery

### Dashboard Synchronization

The frontend periodically synchronizes dashboard data with the backend.

A **Sync Now** option is also available for manual synchronization.

---

## Delivery Status Workflow

LiquorFlow enforces the following delivery sequence:

```text
ASSIGNED
    ↓
PICKED_UP
    ↓
OUT_FOR_DELIVERY
    ↓
DELIVERED
```

Invalid status transitions are rejected, providing a predictable workflow and audit trail.

---

## System Architecture

The production system uses a three-service architecture:

```text
                    ┌──────────────────────┐
                    │        Users         │
                    │ Admin / Attendant /  │
                    │ Dispatcher / Rider   │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Render Frontend    │
                    │     React + Vite     │
                    └──────────┬───────────┘
                               │ HTTPS / Axios
                               ▼
                    ┌──────────────────────┐
                    │   Render Backend     │
                    │ FastAPI + SQLAlchemy │
                    │ Auth / RBAC / APIs   │
                    └──────────┬───────────┘
                               │ PostgreSQL
                               ▼
                    ┌──────────────────────┐
                    │  Supabase PostgreSQL │
                    │     Production DB    │
                    └──────────────────────┘
```

**Production database:** Supabase PostgreSQL.

The previous Render PostgreSQL database was retired after the data was backed up, restored to Supabase, and production read/write operations were verified.

See the detailed architecture documentation in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

---

## Technology Stack

### Backend

- **Python 3.14**
- **FastAPI 0.141.1**
- **SQLAlchemy 2.0.52**
- **PostgreSQL**
- **Pydantic 2.13.4**
- **Alembic 1.19.1**
- **PyJWT 2.13.0**
- **pwdlib / Argon2**
- **Uvicorn**

### Frontend

- **React**
- **Vite 8.2.2**
- **Axios**
- **React Router**

### Development & Deployment

- **Git**
- **GitHub**
- **Render**
- **Supabase**
- REST API
- JWT Authentication

---

## Project Structure

```text
LiquorFlow/
│
├── backend/
│   ├── app/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── routes/
│   │   ├── services/
│   │   ├── database.py
│   │   └── main.py
│   │
│   ├── alembic/
│   ├── tests/
│   ├── requirements.txt
│   └── ...
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── api/
│   │   └── ...
│   │
│   ├── package.json
│   └── ...
│
├── docs/
│   ├── ARCHITECTURE.md
│   └── screenshots/
│
└── README.md
```

---

## Core Data Models

### User

```text
id
name
email
phone
password_hash
role
is_active
created_at
updated_at
```

Supported roles:

```text
ADMIN
ATTENDANT
DISPATCHER
RIDER
```

### Customer

```text
id
name
phone
address
```

### Product

```text
id
name
category
price
stock_quantity
is_active
```

### Order

```text
id
customer_id
created_by
delivery_address
total_amount
status
created_at
updated_at
```

### Order Item

```text
id
order_id
product_id
quantity
unit_price
subtotal
```

### Delivery

```text
id
order_id
rider_id
assigned_by
assigned_at
picked_up_at
out_for_delivery_at
delivered_at
proof_of_delivery
created_at
updated_at
```

---

## Database & Migration

LiquorFlow uses **PostgreSQL** as its relational database and **Alembic** for schema migrations.

### Production database

The production database is hosted on **Supabase PostgreSQL**.

The migration from the original Render PostgreSQL database was completed using this process:

1. Created the Supabase PostgreSQL project.
2. Created a backup of the existing Render database.
3. Restored the backup into Supabase.
4. Verified the migrated tables and data.
5. Updated the Render backend `DATABASE_URL` to Supabase.
6. Verified production API reads.
7. Verified production writes by creating an order and completing the rider delivery workflow.
8. Removed temporary database diagnostics.
9. Rotated the production database credentials.
10. Verified the application again after credential rotation.
11. Retired the previous Render PostgreSQL database.

A local recovery dump was retained during the migration process.

---

## Security

LiquorFlow implements several security controls:

- JWT authentication
- Password hashing
- Protected API routes
- Role-based authorization
- Rider-specific delivery access
- Dispatcher/admin delivery management
- Input validation with Pydantic
- Duplicate delivery assignment protection
- Sequential delivery status validation
- Environment-based production configuration

Production credentials and secrets are stored through environment variables and are not committed to the repository.

---

## Testing

The backend test suite contains automated tests covering major application functionality.

### Current test result

```text
71 passed
```

The tests cover areas including:

- Authentication
- User roles
- Products
- Orders
- Deliveries
- Delivery status transitions
- Authorization
- Duplicate assignments
- API behavior

In addition to automated tests, the production workflow was manually verified after the database migration and credential rotation.

---

## Live Application

### Frontend

[LiquorFlow Live Demo](https://liquorflow-frontend.onrender.com)

### Backend API

[LiquorFlow Backend API](https://liquorflow-backend.onrender.com)

### API Documentation

[LiquorFlow API Documentation](https://liquorflow-backend.onrender.com/docs)

### GitHub Repository

[johnloreng/LiquorFlow](https://github.com/johnloreng/LiquorFlow)

---

## Running Locally

### Prerequisites

Make sure you have:

- Python 3.14+
- Node.js
- PostgreSQL
- Git

### 1. Clone the repository

```bash
git clone https://github.com/johnloreng/LiquorFlow.git
cd LiquorFlow
```

### 2. Backend setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file containing the required database and authentication configuration.

**Do not commit `.env` or production secrets to GitHub.**

Run migrations:

```bash
alembic upgrade head
```

Start the backend:

```bash
uvicorn app.main:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

### 3. Frontend setup

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:5173
```

---

## Running Tests

From the backend directory with the virtual environment activated:

```bash
pytest
```

Expected result for the current test suite:

```text
71 passed
```

---

## Deployment

LiquorFlow is deployed with **Render** for the frontend and backend, and **Supabase** for PostgreSQL.

```text
                    Production
                        │
        ┌───────────────┴───────────────┐
        ▼                               ▼
 Render Frontend                  Render Backend
 React + Vite                     FastAPI
        │                               │
        └──────────── HTTPS ────────────┘
                                        │
                                        ▼
                                Supabase PostgreSQL
```

The backend uses Alembic migrations during deployment and production environment variables for configuration.

The previous Render PostgreSQL database has been retired.

---

## Demonstrated Production Workflow

The completed production workflow has been manually verified:

```text
ADMIN / ATTENDANT
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
                       ├── Picked Up
                       │
                       ├── Out for Delivery
                       │
                       └── Delivered
                               │
                               ▼
                       Proof of Delivery
```

This demonstrates the core MVP from order creation through delivery completion.

---

## Reflex Project

LiquorFlow was developed as part of **Reflex — The Readiness Sprint**.

The project focuses on solving a real operational problem faced by small retailers by transforming an informal delivery coordination process into a structured digital workflow.

### MVP Goals

- Centralize delivery requests
- Improve delivery visibility
- Assign responsibility to riders
- Track delivery status
- Provide proof of delivery
- Demonstrate a working full-stack solution

---

## Future Improvements

With additional development time, LiquorFlow could be extended with:

- Customer search and selection
- Real-time WebSocket synchronization
- SMS/WhatsApp notifications
- GPS rider tracking
- Map-based navigation
- Online payment integration
- Inventory alerts
- Sales analytics
- Delivery performance reports
- Customer order history
- Automated customer notifications

---

## Author

**John Loreng**

GitHub:

[johnloreng/LiquorFlow](https://github.com/johnloreng/LiquorFlow)

---

## Project Status

**Status: Working MVP — Production Deployed**

LiquorFlow is deployed to production and the core workflow has been manually tested from order creation through rider assignment, delivery status updates, and proof of delivery.

The production PostgreSQL database has been migrated from Render to Supabase and verified with live application read/write operations.
