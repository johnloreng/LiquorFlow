from app.database import SessionLocal
from app.models.user import User
from app.models.order import Order

db = SessionLocal()

print("=== USERS ===")
for u in db.query(User).all():
    print(u.id, u.name, u.email, u.role, "active" if u.is_active else "inactive")

print("\n=== ORDERS ===")
for o in db.query(Order).all():
    print(o.id, o.customer_id, o.status)

db.close()