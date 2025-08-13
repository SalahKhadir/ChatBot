#!/usr/bin/env python3
"""
Fix existing users by adding default role
"""

from sqlalchemy.orm import Session
from sqlalchemy import text
from database import SessionLocal
from models import UserRole

def fix_existing_users():
    """Add default role to existing users without role"""
    db: Session = SessionLocal()
    
    try:
        print("🔄 Updating existing users with default role...")
        
        # Update users that have NULL role to default USER role
        result = db.execute(text("""
            UPDATE users 
            SET role = 'USER' 
            WHERE role IS NULL
        """))
        
        print(f"✅ Updated {result.rowcount} users with default role")
        
        # Also update any users that might have empty string role
        result2 = db.execute(text("""
            UPDATE users 
            SET role = 'USER' 
            WHERE role = '' OR role NOT IN ('USER', 'ADMIN')
        """))
        
        if result2.rowcount > 0:
            print(f"✅ Fixed {result2.rowcount} users with invalid roles")
        
        db.commit()
        
        # Show current users with roles
        users_result = db.execute(text("""
            SELECT id, email, full_name, role, is_active 
            FROM users 
            ORDER BY id
        """))
        
        print("\n📋 Current users:")
        print("-" * 80)
        for user in users_result.fetchall():
            status = "✅ Active" if user.is_active else "❌ Inactive"
            role_emoji = "👑" if user.role == "ADMIN" else "👤"
            print(f"{role_emoji} ID: {user.id} | {user.email} | {user.full_name} | Role: {user.role} | {status}")
        
    except Exception as e:
        print(f"❌ Failed to fix users: {e}")
        db.rollback()
        return False
    finally:
        db.close()
    
    return True

if __name__ == "__main__":
    print("🔧 Fixing existing users roles...")
    if fix_existing_users():
        print("🎉 Users roles fixed successfully!")
    else:
        print("❌ Failed to fix users roles!")
