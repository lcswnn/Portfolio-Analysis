import pandas as pd
import numpy as np
from catboost import CatBoostClassifier

# Load features
df = pd.read_csv('../backend/stock_features.csv')
df['date'] = pd.to_datetime(df['date'])
df = df.replace([np.inf, -np.inf], np.nan)
df = df.dropna()

print(f"Loaded {len(df)} samples")

feature_cols = [
    'momentum', 'volatility', 'avg_correlation', 'max_correlation',
    'min_correlation', 'market_correlation', 'sharpe', 'momentum_accel',
    'dividend_yield'
]

# Build correlation matrix from the features data
# Pivot to get tickers as columns, dates as rows, using avg_correlation as proxy
# Or better: build correlation from the feature vectors themselves

def build_correlation_matrix(df):
    """
    Build a correlation matrix between stocks based on their feature profiles over time.
    Stocks with similar feature movements are considered correlated.
    """
    # Pivot: rows = dates, columns = tickers, values = momentum (price movement proxy)
    pivot = df.pivot_table(index='date', columns='ticker', values='momentum', aggfunc='first')
    
    # Calculate correlation between stocks based on how their momentum moves together
    corr_matrix = pivot.corr()
    
    return corr_matrix

print("Building correlation matrix...")
corr_matrix = build_correlation_matrix(df)
print(f"Correlation matrix shape: {corr_matrix.shape}")

# Train model
print("\nTraining CatBoost model...")
model = CatBoostClassifier(
    iterations=200,
    depth=4,
    learning_rate=0.05,
    random_state=42,
    verbose=False
)
model.fit(df[feature_cols], df['beat_market'])
print("Model trained!")

# Get latest data
latest_date = df['date'].max()
latest = df[df['date'] == latest_date].copy()
latest['prob_beat_market'] = model.predict_proba(latest[feature_cols])[:, 1]
print(f"Analyzing {len(latest)} stocks from {latest_date.strftime('%Y-%m-%d')}")


def get_diversified_recommendations(df, corr_matrix, min_prob=0.5, max_correlation=0.5, top_n=20):
    """Get high-probability stocks that are uncorrelated with each other."""
    candidates = df[df['prob_beat_market'] >= min_prob].sort_values(
        'prob_beat_market', ascending=False
    ).copy()
    
    if len(candidates) == 0:
        return pd.DataFrame()
    
    selected = [candidates.iloc[0]['ticker']]
    
    for _, row in candidates.iterrows():
        ticker = row['ticker']
        
        if ticker in selected:
            continue
        
        if len(selected) >= top_n:
            break
        
        # Check correlation with all already-selected stocks
        is_uncorrelated = True
        for selected_ticker in selected:
            if ticker in corr_matrix.columns and selected_ticker in corr_matrix.columns:
                correlation = abs(corr_matrix.loc[ticker, selected_ticker])
                if correlation > max_correlation:
                    is_uncorrelated = False
                    break
            # If ticker not in matrix, allow it (no data to reject it)
        
        if is_uncorrelated:
            selected.append(ticker)
    
    result = candidates[candidates['ticker'].isin(selected)].copy()
    
    # Calculate average correlation with other picks
    avg_corrs = []
    for ticker in result['ticker']:
        other_tickers = [t for t in selected if t != ticker]
        if other_tickers and ticker in corr_matrix.columns:
            corrs = [abs(corr_matrix.loc[ticker, t]) for t in other_tickers if t in corr_matrix.columns]
            avg_corrs.append(np.mean(corrs) if corrs else 0)
        else:
            avg_corrs.append(0)
    
    result['avg_corr_with_picks'] = avg_corrs
    
    return result.sort_values('prob_beat_market', ascending=False)


def get_recommendations(df, min_prob=0.5, min_dividend=0.0, max_volatility=1.0, top_n=20):
    """Get recommendations without diversification filter."""
    filtered = df[
        (df['prob_beat_market'] >= min_prob) &
        (df['dividend_yield'] >= min_dividend) &
        (df['volatility'] <= max_volatility)
    ].copy()
    
    filtered = filtered.sort_values('prob_beat_market', ascending=False)
    return filtered.head(top_n)


def print_recommendations(recs, title="Recommendations", show_corr=False):
    """Pretty print recommendations."""
    print("\n" + "="*90)
    print(title)
    print("="*90)
    
    if show_corr:
        print(f"{'Rank':<5} {'Ticker':<8} {'Prob%':<8} {'Dividend%':<10} {'Momentum':<10} {'Volatility':<10} {'AvgCorr':<10}")
    else:
        print(f"{'Rank':<5} {'Ticker':<8} {'Prob%':<8} {'Dividend%':<10} {'Momentum':<10} {'Volatility':<10}")
    print("-"*90)
    
    for i, (_, row) in enumerate(recs.iterrows(), 1):
        base = (f"{i:<5} {row['ticker']:<8} {row['prob_beat_market']*100:<8.1f} "
                f"{row['dividend_yield']*100:<10.2f} {row['momentum']*100:<10.1f} "
                f"{row['volatility']*100:<10.1f}")
        
        if show_corr and 'avg_corr_with_picks' in row:
            print(f"{base} {row['avg_corr_with_picks']:<10.2f}")
        else:
            print(base)


# ==================== Generate Recommendations ====================

# 1. Standard picks (NOT diversified)
print_recommendations(
    get_recommendations(latest, min_prob=0.5, top_n=20),
    "TOP 20 STOCKS - Highest Probability (NOT diversified)"
)

# 2. Diversified picks (max correlation 0.5)
print_recommendations(
    get_diversified_recommendations(latest, corr_matrix, min_prob=0.5, max_correlation=0.5, top_n=20),
    "TOP 20 DIVERSIFIED STOCKS - High Probability + Low Correlation (<0.5)",
    show_corr=True
)

# 3. Highly diversified picks (max correlation 0.3)
print_recommendations(
    get_diversified_recommendations(latest, corr_matrix, min_prob=0.5, max_correlation=0.3, top_n=15),
    "TOP 15 HIGHLY DIVERSIFIED STOCKS - Very Low Correlation (<0.3)",
    show_corr=True
)

# 4. Diversified dividend picks
diversified_div = get_diversified_recommendations(latest, corr_matrix, min_prob=0.5, max_correlation=0.5, top_n=50)
diversified_div = diversified_div[diversified_div['dividend_yield'] >= 0.02].head(15)
print_recommendations(
    diversified_div,
    "TOP 15 DIVERSIFIED DIVIDEND STOCKS (2%+ yield, <0.5 correlation)",
    show_corr=True
)


# ==================== Summary ====================
print("\n" + "="*90)
print("SUMMARY")
print("="*90)
print(f"Total stocks analyzed: {len(latest)}")
print(f"Stocks with >50% probability: {len(latest[latest['prob_beat_market'] > 0.5])}")
print(f"Stocks with >55% probability: {len(latest[latest['prob_beat_market'] > 0.55])}")


# ==================== Show Correlation of Top Picks ====================
print("\n" + "="*90)
print("CORRELATION MATRIX OF TOP 10 DIVERSIFIED PICKS")
print("="*90)

top_diversified = get_diversified_recommendations(latest, corr_matrix, min_prob=0.5, max_correlation=0.5, top_n=10)
pick_tickers = top_diversified['ticker'].tolist()

# Filter to tickers that exist in correlation matrix
valid_tickers = [t for t in pick_tickers if t in corr_matrix.columns]
if valid_tickers:
    picks_corr = corr_matrix.loc[valid_tickers, valid_tickers]
    print(picks_corr.round(2).to_string())
else:
    print("No valid tickers found in correlation matrix")


# ==================== Export ====================
# Export diversified recommendations
diversified_export = get_diversified_recommendations(latest, corr_matrix, min_prob=0.5, max_correlation=0.5, top_n=50)
diversified_export[['ticker', 'prob_beat_market', 'dividend_yield', 'momentum', 'volatility', 'avg_corr_with_picks']].to_csv(
    'diversified_recommendations.csv', index=False
)
print(f"\nExported to 'diversified_recommendations.csv'")