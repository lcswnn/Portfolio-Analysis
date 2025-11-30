import sqlite3
import os

# Get the database path
db_path = os.path.join(os.path.dirname(__file__), 'data', 'portfolio.db')

# Connect to the database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Delete all records from positions table
cursor.execute("DELETE FROM positions")
print(f"Deleted {cursor.rowcount} records from positions table")

# Delete all records from uploaded_files table
cursor.execute("DELETE FROM uploaded_files")
print(f"Deleted {cursor.rowcount} records from uploaded_files table")

# Commit the changes
conn.commit()

# Close the connection
conn.close()

print("\nDatabase tables reset successfully!")
