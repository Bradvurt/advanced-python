# Create admin user (run in Python shell)
from app.database import SessionLocal
from app.models import User
from app.auth import get_password_hash

db = SessionLocal()
admin = User(
    username="admin",
    email="admin@example.com",
    hashed_password=get_password_hash("admin123"),
    role="admin"
)
db.add(admin)
db.commit()
db.close()