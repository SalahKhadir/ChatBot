#!/usr/bin/env python3
"""
Fix enum values in database to match Python enum
"""

from sqlalchemy.orm import Session
from sqlalchemy import text
from database import SessionLocal

def fix_enum_values():
    """Fix the role enum values to match Python enum"""
    db: Session = SessionLocal()
    
    try:
        print("🔄 Fixing role enum values...")
        
        # Drop and recreate the enum column with correct values
        db.execute(text("""
            ALTER TABLE users 
            MODIFY COLUMN role ENUM('USER', 'ADMIN') NOT NULL DEFAULT 'USER'
        """))
        
        db.commit()
        print("✅ Enum values fixed successfully")
        
    except Exception as e:
        print(f"❌ Failed to fix enum: {e}")
        db.rollback()
        return False
    finally:
        db.close()
    
    return True

if __name__ == "__main__":
    print("🔧 Fixing enum values...")
    if fix_enum_values():
        print("🎉 Enum values fixed successfully!")
    else:
        print("❌ Failed to fix enum values!")
