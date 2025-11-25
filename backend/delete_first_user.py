#!/usr/bin/env python3
"""
Utility script to delete a user from the User table in portfolio.db
Usage: Change the USER_ID variable below and run: python delete_first_user.py
"""

import sqlite3

# ===== CHANGE THIS VARIABLE TO DELETE A DIFFERENT USER =====
USER_ID = 2  # Set this to the ID of the user you want to delete
# ===========================================================

def delete_user(user_id):
    """Delete a user by ID from the User table"""
    db_path = '/Users/lucaswaunn/projects/Portfolio-Analysis/backend/data/portfolio.db'

    try:
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()

        # Check if user exists
        cursor.execute('SELECT id FROM user WHERE id = ?', (user_id,))
        if cursor.fetchone():
            cursor.execute('DELETE FROM user WHERE id = ?', (user_id,))
            connection.commit()
            print(f"✓ Successfully deleted user with ID: {user_id}")
        else:
            print(f"✗ No user found with ID: {user_id}")

        connection.close()

    except sqlite3.Error as e:
        print(f"✗ Database error: {e}")
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == '__main__':
    delete_user(USER_ID)
