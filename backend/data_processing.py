#simple data processing packages
import pandas as pd
import numpy as np

#connect database
import sqlite3

#visualization packages
import matplotlib.pyplot as plt
import seaborn as sns

# load data into sqlite3 database
connection = sqlite3.connect('data/portfolio_analysis.db')

# Load CSV into a DataFrame
df = pd.read_csv('/Users/lucaswaunn/projects/Portfolio-Analysis/data/Positions_Dummy.csv', skiprows=3)
df2 = pd.read_csv('/Users/lucaswaunn/projects/Portfolio-Analysis/data/Positions_Dummy_Nov13.csv', skiprows=3)
df3 = pd.read_csv('/Users/lucaswaunn/projects/Portfolio-Analysis/data/Positions_Dummy_Nov20.csv', skiprows=3)

#drop the last column
df = df.iloc[:, :-1]
df2 = df2.iloc[:, :-1]
df3 = df3.iloc[:, :-1]

# Write to database
df.to_sql('portfolio_analysis.db', connection, if_exists='replace', index=False)
print(f"Loaded {len(df)} rows into positions table.")

# APPEND the additional future data
df2.to_sql('portfolio_analysis.db', connection, if_exists='append', index=False)
print(f"Added {len(df2)} rows to positions table.")

df3.to_sql('portfolio_analysis.db', connection, if_exists='append', index=False)
print(f"Added {len(df3)} rows to positions table.")

#print the database to check data load
query = "SELECT * FROM 'portfolio_analysis.db'"
result = pd.read_sql_query(query, connection)
print(result)

# Close the connection
connection.close()
print("Database connection closed. Loading complete")








