import xgboost as xgb
import lightgbm as lgb
from catboost import CatBoostClassifier
from sklearn.ensemble import VotingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import StandardScaler
import pandas as pd
import numpy as np

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping

# Load features
df = pd.read_csv('stock_features.csv')
df['date'] = pd.to_datetime(df['date'])

# Clean data - remove NaN and infinite values
df = df.replace([np.inf, -np.inf], np.nan)
df = df.dropna()

sorted_dates = df['date'].sort_values().unique()
print(f"Date range: {sorted_dates[0]} to {sorted_dates[-1]}")
print(f"Total unique dates: {len(sorted_dates)}")
print(f"Total samples after cleaning: {len(df)}")

feature_cols = [
    'momentum', 'volatility', 'avg_correlation', 'max_correlation',
    'min_correlation', 'market_correlation', 'sharpe', 'momentum_accel',
    'dividend_yield'
]

split_idx = int(len(sorted_dates) * 0.7)
split_date = sorted_dates[split_idx]

train = df[df['date'] <= split_date]
test = df[df['date'] > split_date]

print(f"\nSplit date: {split_date}")
print(f"Training samples: {len(train)}")
print(f"Test samples: {len(test)}")

X_train, y_train = train[feature_cols], train['beat_market']
X_test, y_test = test[feature_cols], test['beat_market']

# ==================== XGBoost ====================
print("\n" + "="*60)
print("XGBoost")
print("="*60)

model_xgb = xgb.XGBClassifier(
    n_estimators=100,
    max_depth=5,
    learning_rate=0.1,
    random_state=42
)
model_xgb.fit(X_train, y_train)
acc_xgb = accuracy_score(y_test, model_xgb.predict(X_test))
print(f"Accuracy: {acc_xgb:.2%}")

# ==================== LightGBM ====================
print("\n" + "="*60)
print("LightGBM")
print("="*60)

model_lgb = lgb.LGBMClassifier(
    n_estimators=200,
    max_depth=3,
    learning_rate=0.05,
    num_leaves=15,
    random_state=42,
    verbose=-1
)
model_lgb.fit(X_train, y_train)
acc_lgb = accuracy_score(y_test, model_lgb.predict(X_test))
print(f"Accuracy: {acc_lgb:.2%}")

# ==================== CatBoost ====================
print("\n" + "="*60)
print("CatBoost")
print("="*60)

model_cat = CatBoostClassifier(
    iterations=200,
    depth=4,
    learning_rate=0.05,
    random_state=42,
    verbose=False
)
model_cat.fit(X_train, y_train)
acc_cat = accuracy_score(y_test, model_cat.predict(X_test))
print(f"Accuracy: {acc_cat:.2%}")

# ==================== Ensemble ====================
print("\n" + "="*60)
print("Ensemble (XGBoost + LightGBM + CatBoost)")
print("="*60)

ensemble = VotingClassifier(
    estimators=[
        ('xgb', xgb.XGBClassifier(n_estimators=100, max_depth=5, random_state=42)),
        ('lgb', lgb.LGBMClassifier(n_estimators=200, max_depth=3, verbose=-1, random_state=42)),
        ('cat', CatBoostClassifier(iterations=200, depth=4, verbose=False, random_state=42))
    ],
    voting='soft'
)
ensemble.fit(X_train, y_train)
acc_ensemble = accuracy_score(y_test, ensemble.predict(X_test))
print(f"Accuracy: {acc_ensemble:.2%}")

# ==================== LSTM (fixed) ====================
print("\n" + "="*60)
print("LSTM")
print("="*60)

def create_sequences(df, feature_cols, sequence_length=3):
    X_sequences = []
    y_sequences = []
    
    for ticker in df['ticker'].unique():
        ticker_data = df[df['ticker'] == ticker].sort_values('date')
        
        if len(ticker_data) < sequence_length + 1:
            continue
        
        features = ticker_data[feature_cols].values
        targets = ticker_data['beat_market'].values
        
        for i in range(len(ticker_data) - sequence_length):
            X_sequences.append(features[i:i + sequence_length])
            y_sequences.append(targets[i + sequence_length])
    
    return np.array(X_sequences), np.array(y_sequences)

# Scale features
scaler = StandardScaler()
df_scaled = df.copy()
df_scaled[feature_cols] = scaler.fit_transform(df[feature_cols])

# Replace any remaining NaN after scaling
df_scaled[feature_cols] = df_scaled[feature_cols].fillna(0)

train_scaled = df_scaled[df_scaled['date'] <= split_date]
test_scaled = df_scaled[df_scaled['date'] > split_date]

X_train_seq, y_train_seq = create_sequences(train_scaled, feature_cols, 3)
X_test_seq, y_test_seq = create_sequences(test_scaled, feature_cols, 3)

# Replace any NaN in sequences
X_train_seq = np.nan_to_num(X_train_seq, nan=0.0, posinf=0.0, neginf=0.0)
X_test_seq = np.nan_to_num(X_test_seq, nan=0.0, posinf=0.0, neginf=0.0)

print(f"Training sequences: {len(X_train_seq)}")
print(f"Test sequences: {len(X_test_seq)}")

if len(X_train_seq) > 0 and len(X_test_seq) > 0:
    model_lstm = Sequential([
        LSTM(32, return_sequences=True, input_shape=(3, len(feature_cols))),
        Dropout(0.2),
        LSTM(16),
        Dropout(0.2),
        Dense(8, activation='relu'),
        Dense(1, activation='sigmoid')
    ])
    
    model_lstm.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    
    early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
    
    model_lstm.fit(
        X_train_seq, y_train_seq,
        epochs=50,
        batch_size=64,
        validation_split=0.2,
        callbacks=[early_stop],
        verbose=0  # Suppress epoch output
    )
    
    loss, acc_lstm = model_lstm.evaluate(X_test_seq, y_test_seq, verbose=0)
    print(f"Accuracy: {acc_lstm:.2%}")
else:
    acc_lstm = 0

# ==================== Summary ====================
print("\n" + "="*60)
print("SUMMARY")
print("="*60)
results = {
    'XGBoost': acc_xgb,
    'LightGBM': acc_lgb,
    'CatBoost': acc_cat,
    'Ensemble': acc_ensemble,
    'LSTM': acc_lstm
}

for name, acc in sorted(results.items(), key=lambda x: x[1], reverse=True):
    print(f"{name:12} {acc:.2%}")

print(f"\nBest model: {max(results, key=results.get)}")