import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from matplotlib.figure import Figure

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
    
    # Create Figure object (NOT plt.figure)
    fig = Figure(figsize=(10, 6))
    axis = fig.add_subplot(1, 1, 1)
    
    # Plot on the axis
    axis.plot(df['Date'], df['Total_Market_Value'], marker='o', linewidth=2, markersize=8)
    axis.set_title('Portfolio Market Value Over Time')
    axis.set_xlabel('Date')
    axis.set_ylabel('Total Market Value ($)')
    axis.tick_params(axis='x', rotation=45)
    axis.grid(True, alpha=0.3)
    
    fig.tight_layout()
    
    return fig  # RETURN the figure, don't show it

def graph_allocation():
    # Connect to database
    connection = sqlite3.connect('data/positions.db')
    
    # Query to get latest allocation by security type
    query = """
    SELECT "Security Type", 
    SUM(REPLACE(REPLACE("Mkt Val (Market Value)", '$', ''), ',', '')) as Total_Value
    FROM positions
    WHERE "Mkt Val (Market Value)" != '--'
    AND Date = (SELECT MAX(Date) FROM positions)
    GROUP BY "Security Type"
    """
    df = pd.read_sql_query(query, connection)
    connection.close()
    
    # Convert to numeric
    df['Total_Value'] = pd.to_numeric(df['Total_Value'])
    
    # Create Figure object
    fig = Figure(figsize=(10, 6))
    axis = fig.add_subplot(1, 1, 1)
    
    # Create pie chart
    axis.pie(df['Total_Value'], labels=df['Security Type'], autopct='%1.1f%%', startangle=90)
    axis.set_title('Portfolio Allocation by Security Type')
    
    return fig

class Analytics:
    def __init__(self, value):
        self.value = value
    
    def get_value(self):
        return self.value * 2