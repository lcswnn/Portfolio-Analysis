import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

# Connect to the SQLite database
connection = sqlite3.connect('data/positions.db')
cursor = connection.cursor()

def graph_data():
    # Connect to database
    connection = sqlite3.connect('data/positions.db')
    
    # Query to get market value grouped by dates
    query = """
    SELECT Date, SUM(REPLACE(REPLACE("Mkt Val (Market Value)", '$', ''), ',', '')) as Total_Market_Value
    FROM positions
    WHERE "Mkt Val (Market Value)" != '--'
    GROUP BY Date
    ORDER BY Date
    """
    df = pd.read_sql_query(query, connection)
    connection.close()
    
    # Convert to numeric
    df['Total_Market_Value'] = pd.to_numeric(df['Total_Market_Value'])
    
    # Plot market value over time
    plt.figure(figsize=(10, 6))
    plt.plot(df['Date'], df['Total_Market_Value'], marker='o', linewidth=2, markersize=8)
    plt.title('Portfolio Market Value Over Time')
    plt.xlabel('Date')
    plt.ylabel('Total Market Value ($)')
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()

class Analytics:
  def __init__(self, value):
    self.value = value
    
  def get_value(self):
    return self.value * 2