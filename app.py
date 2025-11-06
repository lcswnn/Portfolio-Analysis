#simple data processing packages
import pandas as pd
import numpy as np

#visualization packages
import matplotlib.pyplot as plt
import seaborn as sns

# Load dataset
data = pd.read_csv('/Users/lucaswaunn/projects/Portfolio-Analysis/positions/Positions_Dummy.csv', skiprows=3)
data_formatted = data.iloc[:, :-1]
data2 = pd.read_csv('/Users/lucaswaunn/projects/Portfolio-Analysis/positions/Positions_Dummy.csv', skiprows=3)
data2_formatted = data2.iloc[:, :-1]
data3 = pd.read_csv('/Users/lucaswaunn/projects/Portfolio-Analysis/positions/Positions_Dummy.csv', skiprows=3)
data3_formatted = data3.iloc[:, :-1]
data = data.dropna(how='all')  # Drop rows where all elements are NaN
print(data_formatted, data2_formatted, data3_formatted)



