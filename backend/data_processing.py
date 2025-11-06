#os
import os
csv_dir = '/Users/lucaswaunn/projects/Portfolio-Analysis/csv_imports/'

#data processing packages
import pandas as pd
import numpy as np
import sqlite3
import re

#visualization packages
import matplotlib.pyplot as plt
import seaborn as sns

# load data into sqlite3 database
connection = sqlite3.connect('data/positions.db')

# Function to extract date and load CSV
def load_csv_with_date(file_path):
    # Read first line to get the date
    with open(file_path, 'r') as f:
        first_line = f.readline().strip()
        # Use regex to find date pattern MM/DD/YYYY
        date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', first_line)
        date_str = date_match[1] if date_match else "Unknown"
    
    # Load CSV into DataFrame
    df = pd.read_csv(file_path, skiprows=3)
    # Drop the last column
    df = df.iloc[:, :-1]
    # Add date column
    df['Date'] = date_str
    return df
  
def load_csv_to_db():
  directory = os.fsencode(csv_dir)
  for file in os.listdir(directory):
    if file == os.listdir(directory)[0]:
      filename = os.fsdecode(file)
      if filename.endswith('.csv'):
          file_path = os.path.join(csv_dir, filename)
          df = load_csv_with_date(file_path)
          df.to_sql('positions', connection, if_exists='replace', index=False)
          print(f"Added {len(df)} rows from {df['Date'].iloc[0]}")
      else:
          continue
    else:
      filename = os.fsdecode(file)
      if filename.endswith('.csv'):
          file_path = os.path.join(csv_dir, filename)
          df = load_csv_with_date(file_path)
          df.to_sql('positions', connection, if_exists='append', index=False)
          print(f"Added {len(df)} rows from {df['Date'].iloc[0]}")

load_csv_to_db()

# Close the connection
connection.close()
print("Database connection closed. Loading complete")