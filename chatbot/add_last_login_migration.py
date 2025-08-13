#!/usr/bin/env python3
"""
Migration script to add last_login column to users table
"""
import mysql.connector
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "chatbot")

def main():
    try:
        # Connect to MySQL database
        connection = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci'
        )
        
        cursor = connection.cursor()
        
        # Check if last_login column exists
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'users' AND COLUMN_NAME = 'last_login'
        """, (DB_NAME,))
        
        result = cursor.fetchone()
        
        if result:
            print("✅ Column 'last_login' already exists in users table")
        else:
            print("🔧 Adding 'last_login' column to users table...")
            
            # Add last_login column
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN last_login DATETIME NULL AFTER is_active
            """)
            
            connection.commit()
            print("✅ Successfully added 'last_login' column to users table")
        
        cursor.close()
        connection.close()
        print("🎉 Migration completed successfully!")
        
    except mysql.connector.Error as error:
        print(f"❌ Database error: {error}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
