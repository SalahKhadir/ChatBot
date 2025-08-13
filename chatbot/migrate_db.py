#!/usr/bin/env python3
"""
Database migration script to add the role column to existing users table
"""

import sys
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import SessionLocal, engine
import models

def migrate_database():
    """Add role column to existing users table"""
    db: Session = SessionLocal()
    
    try:
        # Check if role column already exists
        result = db.execute(text("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'users' 
            AND COLUMN_NAME = 'role'
            AND TABLE_SCHEMA = DATABASE()
        """))
        
        role_exists = result.fetchone()
        
        if role_exists:
            print("✅ Role column already exists in users table")
        else:
            print("🔄 Adding role column to users table...")
            # Add role column with default value
            db.execute(text("""
                ALTER TABLE users 
                ADD COLUMN role ENUM('user', 'admin') NOT NULL DEFAULT 'user'
            """))
            db.commit()
            print("✅ Role column added successfully")
        
        # Create all tables (in case some are missing)
        models.Base.metadata.create_all(bind=engine)
        print("✅ All database tables are up to date")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        db.rollback()
        return False
    finally:
        db.close()
    
    return True

def check_database_connection():
    """Check if database connection is working"""
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 CGI ChatBot - Database Migration")
    print("-" * 40)
    
    # Check database connection
    print("🔍 Checking database connection...")
    if not check_database_connection():
        print("💡 Make sure your MySQL server is running and the database exists.")
        sys.exit(1)
    
    print("✅ Database connection successful")
    
    # Run migration
    if migrate_database():
        print("🎉 Database migration completed successfully!")
    else:
        print("❌ Migration failed!")
        sys.exit(1)
