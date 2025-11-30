import pandas as pd
import numpy as np
from catboost import CatBoostClassifier
import yfinance as yf

# Load and clean data
df = pd.read_csv('../backend/stock_features.csv')
df['date'] = pd.to_datetime(df['date'])
df = df.replace([np.inf, -np.inf], np.nan)
df = df.dropna()

print(f"Loaded {len(df)} samples")
print(f"Date range: {df['date'].min()} to {df['date'].max()}")

feature_cols = [
    'momentum', 'volatility', 'avg_correlation', 'max_correlation',
    'min_correlation', 'market_correlation', 'sharpe', 'momentum_accel',
    'dividend_yield'
]

# Train CatBoost on all data
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

# Get most recent data for each stock
latest_date = df['date'].max()
latest = df[df['date'] == latest_date].copy()
print(f"\nAnalyzing {len(latest)} stocks from {latest_date.strftime('%Y-%m-%d')}")

# Predict probability of beating market
latest['prob_beat_market'] = model.predict_proba(latest[feature_cols])[:, 1]


def get_recommendations(df, min_prob=0.5, min_dividend=0.0, max_volatility=1.0, top_n=20):
    """
    Filter and rank stocks based on criteria.
    
    Parameters:
    - min_prob: Minimum probability of beating market (0.5 = 50%)
    - min_dividend: Minimum dividend yield (0.02 = 2%)
    - max_volatility: Maximum annualized volatility (0.4 = 40%)
    - top_n: Number of stocks to return
    """
    filtered = df[
        (df['prob_beat_market'] >= min_prob) &
        (df['dividend_yield'] >= min_dividend) &
        (df['volatility'] <= max_volatility)
    ].copy()
    
    # Sort by probability
    filtered = filtered.sort_values('prob_beat_market', ascending=False)
    
    return filtered.head(top_n)


def fetch_current_prices(tickers):
    """Fetch current prices for tickers."""
    prices = {}
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            prices[ticker] = stock.info.get('currentPrice', stock.info.get('regularMarketPrice', None))
        except:
            prices[ticker] = None
    return prices


def print_recommendations(recs, title="Stock Recommendations"):
    """Pretty print recommendations."""
    print("\n" + "="*80)
    print(title)
    print("="*80)
    print(f"{'Rank':<5} {'Ticker':<8} {'Prob%':<8} {'Dividend%':<10} {'Momentum':<10} {'Volatility':<10}")
    print("-"*80)
    
    for i, (_, row) in enumerate(recs.iterrows(), 1):
        print(f"{i:<5} {row['ticker']:<8} {row['prob_beat_market']*100:<8.1f} "
              f"{row['dividend_yield']*100:<10.2f} {row['momentum']*100:<10.1f} "
              f"{row['volatility']*100:<10.1f}")


# ==================== Generate Recommendations ====================

# 1. Top picks overall (highest probability)
print_recommendations(
    get_recommendations(latest, min_prob=0.5, top_n=20),
    "TOP 20 STOCKS - Highest Probability of Beating Market"
)

# 2. Dividend-focused picks (good dividends + likely to beat market)
print_recommendations(
    get_recommendations(latest, min_prob=0.5, min_dividend=0.02, top_n=15),
    "TOP 15 DIVIDEND STOCKS (2%+ yield) - Likely to Beat Market"
)

# 3. Conservative picks (lower volatility + likely to beat market)
print_recommendations(
    get_recommendations(latest, min_prob=0.5, max_volatility=0.3, top_n=15),
    "TOP 15 LOW-VOLATILITY STOCKS - Conservative Picks"
)

# 4. High-conviction picks (highest probability + dividend)
print_recommendations(
    get_recommendations(latest, min_prob=0.55, min_dividend=0.01, top_n=10),
    "TOP 10 HIGH-CONVICTION PICKS (55%+ prob, 1%+ dividend)"
)

# ==================== Summary Stats ====================
print("\n" + "="*80)
print("SUMMARY STATISTICS")
print("="*80)
print(f"Total stocks analyzed: {len(latest)}")
print(f"Stocks with >50% probability: {len(latest[latest['prob_beat_market'] > 0.5])}")
print(f"Stocks with >55% probability: {len(latest[latest['prob_beat_market'] > 0.55])}")
print(f"Stocks with >60% probability: {len(latest[latest['prob_beat_market'] > 0.6])}")

print(f"\nAverage probability: {latest['prob_beat_market'].mean()*100:.1f}%")
print(f"Max probability: {latest['prob_beat_market'].max()*100:.1f}%")
print(f"Min probability: {latest['prob_beat_market'].min()*100:.1f}%")

# ==================== Export to CSV ====================
# Export all predictions
latest_export = latest[['ticker', 'prob_beat_market', 'dividend_yield', 'momentum', 
                        'volatility', 'sharpe', 'avg_correlation']].copy()
latest_export = latest_export.sort_values('prob_beat_market', ascending=False)
latest_export.to_csv('all_stock_predictions.csv', index=False)
print(f"\nExported all predictions to 'all_stock_predictions.csv'")

# Export top picks
top_picks = get_recommendations(latest, min_prob=0.5, top_n=50)
top_picks[['ticker', 'prob_beat_market', 'dividend_yield', 'momentum', 'volatility']].to_csv(
    'top_stock_picks.csv', index=False
)
print("Exported top 50 picks to 'top_stock_picks.csv'")