#!/usr/bin/env python3
"""
Migration script to consolidate databases into single portfolio.db
Transfers User data from account-info.db and Position data from positions.db
"""

import sqlite3
import os
from pathlib import Path

DATA_DIR = Path('/Users/lucaswaunn/projects/Portfolio-Analysis/backend/data')
OLD_ACCOUNT_DB = DATA_DIR / 'account-info.db'
OLD_POSITIONS_DB = DATA_DIR / 'positions.db'
NEW_DB = DATA_DIR / 'portfolio.db'

def migrate_databases():
    """Migrate data from old databases to new consolidated database"""

    # Connect to old databases
    account_conn = sqlite3.connect(OLD_ACCOUNT_DB)
    positions_conn = sqlite3.connect(OLD_POSITIONS_DB)

    # Connect to new database (will be created if doesn't exist)
    new_conn = sqlite3.connect(NEW_DB)
    new_cursor = new_conn.cursor()

    try:
        # Create tables in new database
        print("Creating tables in new database...")

        # Create user table
        new_cursor.execute('''
            CREATE TABLE IF NOT EXISTS user (
                id INTEGER PRIMARY KEY,
                firstname VARCHAR(30) NOT NULL,
                lastname VARCHAR(30) NOT NULL,
                email VARCHAR(50) UNIQUE NOT NULL,
                username VARCHAR(20) UNIQUE NOT NULL,
                password VARCHAR(80) NOT NULL
            )
        ''')

        # Create positions table
        new_cursor.execute('''
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY,
                Symbol VARCHAR(50),
                Description VARCHAR(500),
                Qty_Quantity VARCHAR(100),
                Price VARCHAR(100),
                Price_Chng_Dollar VARCHAR(100),
                Price_Chng_Percent VARCHAR(100),
                Mkt_Val VARCHAR(100),
                Day_Chng_Dollar VARCHAR(100),
                Day_Chng_Percent VARCHAR(100),
                Cost_Basis VARCHAR(100),
                Gain_Dollar VARCHAR(100),
                Gain_Percent VARCHAR(100),
                Reinvest VARCHAR(50),
                Reinvest_Capital_Gains VARCHAR(50),
                Security_Type VARCHAR(100),
                Date VARCHAR(50)
            )
        ''')

        new_conn.commit()
        print("Tables created successfully")

        # Migrate user data
        print("\nMigrating user data...")
        account_cursor = account_conn.cursor()
        account_cursor.execute('SELECT id, firstname, lastname, email, username, password FROM user')
        users = account_cursor.fetchall()

        for user in users:
            new_cursor.execute('''
                INSERT INTO user (id, firstname, lastname, email, username, password)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', user)

        new_conn.commit()
        print(f"Migrated {len(users)} user(s)")

        # Migrate position data
        print("\nMigrating position data...")
        positions_cursor = positions_conn.cursor()
        positions_cursor.execute('''
            SELECT id, Symbol, Description, Qty_Quantity, Price, Price_Chng_Dollar,
                   Price_Chng_Percent, Mkt_Val, Day_Chng_Dollar, Day_Chng_Percent,
                   Cost_Basis, Gain_Dollar, Gain_Percent, Reinvest,
                   Reinvest_Capital_Gains, Security_Type, Date
            FROM positions
        ''')
        positions = positions_cursor.fetchall()

        for position in positions:
            new_cursor.execute('''
                INSERT INTO positions
                (id, Symbol, Description, Qty_Quantity, Price, Price_Chng_Dollar,
                 Price_Chng_Percent, Mkt_Val, Day_Chng_Dollar, Day_Chng_Percent,
                 Cost_Basis, Gain_Dollar, Gain_Percent, Reinvest,
                 Reinvest_Capital_Gains, Security_Type, Date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', position)

        new_conn.commit()
        print(f"Migrated {len(positions)} position(s)")

        print("\n✓ Migration completed successfully!")
        print(f"New database created at: {NEW_DB}")

    except Exception as e:
        new_conn.rollback()
        print(f"\n✗ Migration failed: {str(e)}")
        raise

    finally:
        account_conn.close()
        positions_conn.close()
        new_conn.close()

if __name__ == '__main__':
    print("Starting database consolidation migration...\n")
    migrate_databases()
