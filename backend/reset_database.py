#!/usr/bin/env python3
"""
Database reset script - Clears all data and creates fresh tables.
WARNING: This will delete all user accounts, positions, and uploaded files!
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = 'data/portfolio.db'

def backup_database():
    """Create a backup before reset"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f'data/backup/portfolio_backup_before_reset_{timestamp}.db'

    os.makedirs('data/backup', exist_ok=True)

    with open(DB_PATH, 'rb') as original:
        with open(backup_path, 'wb') as backup:
            backup.write(original.read())

    print(f"✓ Database backed up to: {backup_path}")
    return backup_path

def reset_database():
    """Drop all tables and recreate schema"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        print("\n" + "=" * 60)
        print("RESETTING DATABASE")
        print("=" * 60)

        # Get list of all tables
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table'
        """)
        tables = cursor.fetchall()

        if not tables:
            print("\n⚠ No tables found in database")
        else:
            print(f"\nFound {len(tables)} table(s) to drop:")
            for (table_name,) in tables:
                print(f"  - {table_name}")

        # Drop all tables
        for (table_name,) in tables:
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            print(f"✓ Dropped {table_name}")

        conn.commit()

        print("\n" + "-" * 60)
        print("Creating fresh schema...")
        print("-" * 60)

        # Recreate user table
        cursor.execute("""
            CREATE TABLE user (
                id INTEGER PRIMARY KEY,
                firstname TEXT NOT NULL,
                lastname TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)
        print("✓ Created user table")

        # Recreate positions table
        cursor.execute("""
            CREATE TABLE positions (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                Symbol TEXT,
                Description TEXT,
                Qty_Quantity TEXT,
                Price TEXT,
                Price_Chng_Dollar TEXT,
                Price_Chng_Percent TEXT,
                Mkt_Val TEXT,
                Day_Chng_Dollar TEXT,
                Day_Chng_Percent TEXT,
                Cost_Basis TEXT,
                Gain_Dollar TEXT,
                Gain_Percent TEXT,
                Reinvest TEXT,
                Reinvest_Capital_Gains TEXT,
                Security_Type TEXT,
                Date TEXT,
                FOREIGN KEY (user_id) REFERENCES user(id)
            )
        """)
        print("✓ Created positions table")

        # Recreate uploaded_files table
        cursor.execute("""
            CREATE TABLE uploaded_files (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                upload_date DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                position_count INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES user(id)
            )
        """)
        print("✓ Created uploaded_files table")

        conn.commit()

        print("\n" + "=" * 60)
        print("✅ DATABASE RESET COMPLETE")
        print("=" * 60)
        print("\nYour database is now empty and ready for testing!")
        print("\nNext steps:")
        print("1. Start your Flask app: python app.py")
        print("2. Register new test users")
        print("3. Each user can upload their own CSV files")
        print("4. Test user data isolation and file upload tracking")

        return True

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error: {str(e)}")
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    print("\n⚠️  WARNING: This will DELETE all data from your database!")
    print("   Users: DELETED")
    print("   Positions: DELETED")
    print("   Uploaded Files: DELETED")
    print("\nA backup will be created before deletion.")

    response = input("\nAre you sure you want to reset the database? (type 'yes' to confirm): ")

    if response.lower() == 'yes':
        # Backup first
        backup_database()

        # Reset
        success = reset_database()

        if success:
            print("\nBackup location: data/backup/")
            print("If you need to restore, copy the backup file back to data/portfolio.db")
        exit(0 if success else 1)
    else:
        print("\n❌ Reset cancelled")
        exit(1)
