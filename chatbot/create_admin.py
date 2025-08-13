#!/usr/bin/env python3
"""
Script to create an initial admin user for the CGI ChatBot system
"""

import sys
import os
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import User, UserRole
from auth import get_password_hash

def create_admin_user():
    """Create initial admin user"""
    # Create database session
    db: Session = SessionLocal()
    
    try:
        # Check if any admin already exists
        admin_exists = db.query(User).filter(User.role == UserRole.ADMIN).first()
        if admin_exists:
            print(f"✅ Admin user already exists: {admin_exists.email}")
            print(f"🔑 Role: {admin_exists.role.value}")
            return
        
        # Admin user details
        admin_email = "admin@cgi.ma"
        admin_password = "admin123"  # This should be changed after first login
        admin_name = "CGI Administrator"
        
        # Create admin user
        admin_user = User(
            email=admin_email,
            full_name=admin_name,
            hashed_password=get_password_hash(admin_password),
            role=UserRole.ADMIN,
            is_active=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("\n" + "="*60)
        print("🚀 ADMIN USER CREATED SUCCESSFULLY!")
        print("="*60)
        print(f"📧 Email: {admin_email}")
        print(f"🔑 Password: {admin_password}")
        print(f"👤 Role: {admin_user.role.value}")
        print(f"✅ Status: {'Active' if admin_user.is_active else 'Inactive'}")
        print("="*60)
        print("⚠️  IMPORTANT: Please change the default password after first login!")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()

def check_database_connection():
    """Check if database connection is working"""
    try:
        from sqlalchemy import text
        db = SessionLocal()
        # Simple query to test connection
        db.execute(text("SELECT 1"))
        db.close()
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 CGI ChatBot - Admin User Setup")
    print("-" * 40)
    
    # Check database connection
    print("🔍 Checking database connection...")
    if not check_database_connection():
        print("💡 Make sure your MySQL server is running and the database exists.")
        sys.exit(1)
    
    print("✅ Database connection successful")
    
    # Create admin user
    create_admin_user()
    
    print("\n🎉 Setup complete! You can now use the admin account to access the admin panel.")
