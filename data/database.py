import sqlite3

file_path = 'data/portfolio_analysis.db'

try:
    conn = sqlite3.connect(file_path)
    cursor = conn.cursor()
    print("Database connection successful.")
except sqlite3.Error as e:
    print(f"Database connection failed: {e}")


