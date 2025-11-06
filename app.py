#simple data processing packages
import pandas as pd
import numpy as np

#visualization packages
import matplotlib.pyplot as plt
import seaborn as sns

# Load dataset
data = pd.read_csv('Positions_Dummy.csv', skiprows=3)
data = data.dropna(how='all')  # Drop rows where all elements are NaN
print(data.head())



