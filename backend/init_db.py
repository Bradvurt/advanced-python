#!/usr/bin/env python
"""
Initialize database with default admin user.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.database import SessionLocal, engine, Base
from app.models import User
from app.auth import get_password_hash

def init_database():
    """Create tables and default admin user."""
    
    # Create all tables
    print("🔄 Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created")
    
    # Create default admin user if it doesn't exist
    db = SessionLocal()
    
    admin_username = "admin"
    admin_email = "admin@venuebot.com"
    admin_password = "admin123"  # Change this in production!
    
    existing_admin = db.query(User).filter(
        (User.username == admin_username) | (User.email == admin_email)
    ).first()
    
    if existing_admin:
        print(f"✅ Admin user already exists: {existing_admin.username}")
    else:
        admin_user = User(
            username=admin_username,
            email=admin_email,
            hashed_password=get_password_hash(admin_password),
            role="admin",
            preferences={},
            is_active=True
        )
        db.add(admin_user)
        db.commit()
        print("✅ Default admin user created:")
        print(f"   Username: {admin_username}")
        print(f"   Password: {admin_password}")
        print("   ⚠️  Change this password immediately!")
    
    # Create test user for development
    test_username = "testuser"
    test_email = "test@venuebot.com"
    
    existing_test = db.query(User).filter(
        (User.username == test_username) | (User.email == test_email)
    ).first()
    
    if not existing_test:
        test_user = User(
            username=test_username,
            email=test_email,
            hashed_password=get_password_hash("test123"),
            role="user",
            preferences={
                "categories": ["Restaurants", "Coffee Shops"],
                "price_range": "$$",
                "location": "Downtown"
            },
            is_active=True
        )
        db.add(test_user)
        db.commit()
        print("✅ Test user created: testuser / test123")
    
    db.close()
    print("\n🎉 Database initialization complete!")

if __name__ == "__main__":
    init_database()