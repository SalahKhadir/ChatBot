#!/usr/bin/env python3
"""
Migration script to add last_login column to users table using SQLAlchemy
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment variables
load_dotenv()

# Database configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "chatbot")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

def main():
    try:
        # Create engine
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as connection:
            # Check if last_login column exists
            result = connection.execute(text("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = :db_name AND TABLE_NAME = 'users' AND COLUMN_NAME = 'last_login'
            """), {"db_name": DB_NAME})
            
            if result.fetchone():
                print("✅ Column 'last_login' already exists in users table")
            else:
                print("🔧 Adding 'last_login' column to users table...")
                
                # Add last_login column
                connection.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN last_login DATETIME NULL AFTER is_active
                """))
                
                connection.commit()
                print("✅ Successfully added 'last_login' column to users table")
        
        print("🎉 Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
