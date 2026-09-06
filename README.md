#  LiquorFlow

### Order & Delivery Management System for Small Liquor Retailers

LiquorFlow is a web-based order and delivery management system designed to help small liquor retailers move away from informal WhatsApp/phone-based delivery coordination to a structured, trackable workflow.

The system connects **admin, dispatchers and riders** through role-based access and provides visibility throughout the delivery lifecycle — from order creation to proof of delivery.

---

##  Project Overview

Small retailers often coordinate customer deliveries through phone calls and WhatsApp messages. This can make it difficult to:

* Keep a centralized record of orders
* Know which rider is handling an order
* Track the current delivery status
* Maintain accountability for completed deliveries
* Confirm that a delivery has actually been completed

LiquorFlow addresses these challenges by providing a centralized digital workflow for managing orders and deliveries.

---

##  Solution

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

Every stage is recorded by the system, providing better visibility and accountability.

---

##  User Roles

### Administrator

* Access the management dashboard
* Manage products
* Create customer orders
* Select products
* View orders
* Oversee deliveries
* Manage system users
* View created orders

### Dispatcher

* View orders
* View delivery requests
* Assign riders
* Monitor delivery progress

### Rider

* View assigned deliveries
* Update delivery status
* Confirm pickup
* Mark orders as out for delivery
* Complete deliveries
* Provide proof of delivery

---

##  Key Features

###  Authentication & Authorization

* JWT-based authentication
* Password hashing
* Role-based access control
* Protected API endpoints
* Separate workflows for Admin, Attendant, Dispatcher and Rider

###  Product Management

* Create products
* Manage product prices
* Manage stock quantities
* Activate/deactivate products
* Retrieve active products for order creation

###  Customer Management

* Create customer records
* Store customer name
* Store customer phone number
* Store delivery address

###  Order Management

* Create orders
* Add multiple products to an order
* Specify product quantities
* Automatically calculate order totals
* Track order status
* View orders in the dashboard

###  Delivery Management

* Assign riders to orders
* Prevent duplicate delivery assignments
* Track delivery status
* Enforce sequential delivery transitions
* Record delivery timestamps
* Capture proof of delivery

###  Dashboard Synchronization

The frontend periodically synchronizes with the backend to keep dashboard information updated.

A **Sync Now** option is also available for manual synchronization.

---

##  Delivery Status Workflow

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

This prevents invalid status transitions and provides a clear audit trail of the delivery process.

---

##  System Architecture

```text
                    ┌─────────────────────┐
                    │       User          │
                    │      Admin /        │
                    │Dispatcher / Rider   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   React Frontend    │
                    │      + Vite         │
                    └──────────┬──────────┘
                               │
                         Axios / HTTP
                               │
                               ▼
                    ┌─────────────────────┐
                    │    FastAPI API      │
                    │                     │
                    │ Authentication      │
                    │ RBAC                │
                    │ Orders              │
                    │ Products            │
                    │ Deliveries          │
                    └──────────┬──────────┘
                               │
                        SQLAlchemy ORM
                               │
                               ▼
                    ┌─────────────────────┐
                    │     PostgreSQL      │
                    │      Database       │
                    └─────────────────────┘
```

---

##  Technology Stack

### Backend

* **Python 3.14**
* **FastAPI 0.141.1**
* **SQLAlchemy 2.0.52**
* **PostgreSQL**
* **Pydantic 2.13.4**
* **Alembic 1.19.1**
* **PyJWT 2.13.0**
* **pwdlib / Argon2**
* **Uvicorn**

### Frontend

* **React**
* **Vite 8.2.2**
* **Axios**
* **React Router**

### Development & Deployment

* **Git**
* **GitHub**
* **Render**
* REST API
* JWT Authentication

---

##  Project Structure

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
└── README.md
```

---

##  Core Data Models

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

##  Security

LiquorFlow implements several security controls:

* JWT authentication
* Password hashing
* Protected API routes
* Role-based authorization
* Rider-specific delivery access
* Dispatcher/admin delivery management
* Input validation with Pydantic
* Duplicate delivery assignment protection
* Sequential delivery status validation

Production credentials and secrets are stored through environment variables rather than committed to the repository.

---

##  Testing

The backend test suite contains automated tests covering major application functionality.

### Current test result

```text
71 passed
```

The tests cover areas including:

* Authentication
* User roles
* Products
* Orders
* Deliveries
* Delivery status transitions
* Authorization
* Duplicate assignments
* API behavior

---

##  Live Application

### Frontend

[LiquorFlow Live Demo](https://liquorflow-frontend.onrender.com)

### Backend API

[LiquorFlow Backend API](https://liquorflow-backend.onrender.com)

### API Documentation

[LiquorFlow API Documentation](https://liquorflow-backend.onrender.com)

---

##  Running Locally

### Prerequisites

Make sure you have:

* Python 3.14+
* Node.js
* PostgreSQL
* Git

---

### 1. Clone the repository

```bash
git clone https://github.com/johnloreng/LiquorFlow.git
cd LiquorFlow
```

---

# Backend Setup

### 2. Navigate to backend

```bash
cd backend
```

### 3. Create a virtual environment

```bash
python3 -m venv venv
```

### 4. Activate the environment

```bash
source venv/bin/activate
```

### 5. Install dependencies

```bash
pip install -r requirements.txt
```

### 6. Configure environment variables

Create a `.env` file containing the required database and authentication configuration.

**Do not commit `.env` or production secrets to GitHub.**

### 7. Run database migrations

```bash
alembic upgrade head
```

### 8. Start the backend

```bash
uvicorn app.main:app --reload
```

Backend will be available at:

```text
http://127.0.0.1:8000
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

---

# Frontend Setup

Open another terminal:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

Frontend will normally be available at:

```text
http://localhost:5173
```

---

##  Running Tests

From the backend directory with the virtual environment activated:

```bash
pytest
```

Expected result for the current test suite:

```text
71 passed
```

---

##  Deployment

LiquorFlow is deployed using **Render**.

The production architecture consists of:

```text
React/Vite Frontend
        │
        ▼
     Render
        │
        ▼
FastAPI Backend
        │
        ▼
PostgreSQL Database
```

The backend uses database migrations during deployment and production environment variables for configuration.

---

##  Demonstrated Workflow

The completed production workflow has been manually verified:

```text
ADMIN
  │
  └── Create Order
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

##  Reflex Project

LiquorFlow was developed as part of **Reflex — The Readiness Sprint**.

The project focuses on solving a real operational problem faced by small retailers by transforming an informal delivery coordination process into a structured digital workflow.

### MVP Goals

* Centralize delivery requests
* Improve delivery visibility
* Assign responsibility to riders
* Track delivery status
* Provide proof of delivery
* Demonstrate a working full-stack solution

---

##  Future Improvements

With additional development time, LiquorFlow could be extended with:

* Customer search and selection
* Real-time WebSocket synchronization
* SMS/WhatsApp notifications
* GPS rider tracking
* Map-based navigation
* Online payment integration
* Inventory alerts
* Sales analytics
* Delivery performance reports
* Customer order history
* Automated customer notifications

---

##  Author

**John Loreng**

GitHub:

[johnloreng/LiquorFlow](https://github.com/johnloreng/LiquorFlow)

---

##  Project Status

**Status: Working MVP**

LiquorFlow has been deployed to production and the complete core workflow has been manually tested from order creation through rider assignment, delivery status updates, and proof of delivery.
