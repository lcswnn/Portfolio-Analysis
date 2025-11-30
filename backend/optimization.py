# sourcery skip: use-named-expression
import re
import json
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import xgboost as xgb
import time

large_cap_url = 'https://www.zacks.com/funds/etf/SPY/holding'
mid_cap_url = 'https://www.zacks.com/funds/etf/MDY/holding'
small_cap_url = 'https://www.zacks.com/funds/etf/SPSM/holding'
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

large_data = requests.get(large_cap_url, headers=headers)
mid_data = requests.get(mid_cap_url, headers=headers)
small_data = requests.get(small_cap_url, headers=headers)
large_html_content = large_data.text
mid_html_content = mid_data.text
small_html_content = small_data.text

# The data is in a JavaScript variable - extract it with regex
pattern = r'etf_holdings\.formatted_data\s*=\s*(\[.*?\]);'
large_match = re.search(pattern, large_html_content, re.DOTALL)
med_match = re.search(pattern, mid_html_content, re.DOTALL)
small_match = re.search(pattern, small_html_content, re.DOTALL)

if large_match:
    # Parse the JavaScript array as JSON
    large_data_str = large_match.group(1)
    large_holdings_data = json.loads(large_data_str)
    # Extract symbols from the HTML snippets in each row
    large_symbol_list = []
    
    for row in large_holdings_data:
        # The symbol is in the second column (index 1) as HTML
        symbol_html = row[1]
        # Parse it to extract the symbol text
        symbol_soup = BeautifulSoup(symbol_html, 'html.parser')
        symbol_span = symbol_soup.find('span', class_='hoverquote-symbol')
        if symbol_span:
            large_symbol_list.append(symbol_span.get_text(strip=True))
        else:
            # Some entries just have the symbol as plain text (like "BRK/B")
            large_symbol_list.append(row[1].strip())
    print(f"Found {len(large_symbol_list)} large cap symbols:")
    
if med_match:
    med_data_str = med_match.group(1)
    med_holding_data = json.loads(med_data_str)
    med_symbol_list = []
    for row in med_holding_data:
        symbol_html = row[1]
        symbol_soup = BeautifulSoup(symbol_html, 'html.parser')
        symbol_span = symbol_soup.find('span', class_='hoverquote-symbol')
        if symbol_span:
            med_symbol_list.append(symbol_span.get_text(strip=True))
        else:
            med_symbol_list.append(row[1].strip())
    print(f"Found {len(med_symbol_list)} mid cap symbols:")
    
if small_match:
    small_data_str = small_match.group(1)
    small_holding_data = json.loads(small_data_str)
    small_symbol_list = []
    for row in small_holding_data:
        symbol_html = row[1]
        symbol_soup = BeautifulSoup(symbol_html, 'html.parser')
        symbol_span = symbol_soup.find('span', class_='hoverquote-symbol')
        if symbol_span:
            small_symbol_list.append(symbol_span.get_text(strip=True))
        else:
            small_symbol_list.append(row[1].strip())
    print(f"Found {len(small_symbol_list)} small cap symbols:")

def download_in_batches(tickers, period='5y', interval='1d', batch_size=20, delay=5):
    """Download price data in batches, retrying failures at the end."""
    all_prices = []
    failed_tickers = []
    total_batches = (len(tickers) - 1) // batch_size + 1

    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i + batch_size]
        batch_num = i // batch_size + 1
        print(f"Downloading batch {batch_num}/{total_batches} ({len(batch)} tickers)...")

        try:
            data = yf.download(
                batch, 
                period=period, 
                interval=interval, 
                progress=False, 
                threads=False,
                auto_adjust=True
            )
            if not data.empty:
                if isinstance(data.columns, pd.MultiIndex):
                    prices = data['Close']
                else:
                    prices = data[['Close']]
                    if len(batch) == 1:
                        prices.columns = batch
                # Track which tickers we actually got
                got_tickers = set(prices.columns.tolist())
                if missed := [t for t in batch if t not in got_tickers]:
                    failed_tickers.extend(missed)
                all_prices.append(prices)
            else:
                failed_tickers.extend(batch)
        except Exception as e:
            print(f"  Batch failed: {e}")
            failed_tickers.extend(batch)

        time.sleep(delay)

    # Retry failed tickers
    if failed_tickers:
        print(f"\nRetrying {len(failed_tickers)} failed tickers...")
        time.sleep(10)
        retry_batches = (len(failed_tickers) - 1) // batch_size + 1
        for i in range(0, len(failed_tickers), batch_size):
            batch = failed_tickers[i:i + batch_size]
            batch_num = i // batch_size + 1
            print(f"Retry batch {batch_num}/{retry_batches} ({len(batch)} tickers)...")
            try:
                data = yf.download(
                    batch,
                    period=period,
                    interval=interval,
                    progress=False,
                    threads=False,
                    auto_adjust=True
                )
                if not data.empty:
                    if isinstance(data.columns, pd.MultiIndex):
                        prices = data['Close']
                    else:
                        prices = data[['Close']]
                        if len(batch) == 1:
                            prices.columns = batch
                    all_prices.append(prices)
            except Exception as e:
                print(f"  Retry failed: {e}")
            time.sleep(delay)

    # Combine all data
    if all_prices:
        combined = pd.concat(all_prices, axis=1)
        combined = combined.loc[:, ~combined.columns.duplicated()]
        print(f"\nTotal downloaded: {len(combined.columns)} tickers")
        return combined

    return pd.DataFrame()

def is_valid_ticker(ticker):
    """Filter out invalid ticker symbols."""
    # Valid tickers: 1-5 letters, optionally followed by .A, .B, etc.
    pattern = r'^[A-Z]{1,5}(\.[A-Z])?$'
    return bool(re.match(pattern, ticker))

#now find the uncorrelated stocks
all_tickers = large_symbol_list + med_symbol_list + small_symbol_list
all_tickers = list(set(all_tickers))
print(f"Total unique tickers: {len(all_tickers)}")
all_tickers = large_symbol_list + med_symbol_list + small_symbol_list
all_tickers = list(set(all_tickers))  # Remove duplicates
valid_tickers = [t for t in all_tickers if is_valid_ticker(t)]
invalid_tickers = [t for t in all_tickers if not is_valid_ticker(t)]
print("Adding US Cash Index to Valid Tickers...")
valid_tickers.append('DX-Y.NYB')
print("US Cash Index Added.")
print(f"Valid tickers: {len(valid_tickers)}")
print(f"Filtered out: {invalid_tickers}")

# Download in batches
prices = download_in_batches(valid_tickers, period='5y', interval='1d', batch_size=30, delay=2)

# Filter out bad data
prices = prices.dropna(axis=1, how='all')
min_data_points = 250
prices = prices.dropna(axis=1, thresh=min_data_points)
print(f"Valid tickers remaining: {len(prices.columns)}")

returns = prices.pct_change(fill_method=None).dropna()
corr_matrix = returns.corr()
print(corr_matrix)
print(f"Non-NaN values: {corr_matrix.notna().sum().sum()}")

#get the top 5 lowest correlations
def get_lowest_correlations(corr_matrix, n=20):
    """Get the n lowest positive correlated pairs (>= 0)."""
    # Get upper triangle (avoid duplicates and self-correlations)
    upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
    
    # Stack and sort
    pairs = upper.stack().sort_values()
    
    # Filter to only non-negative correlations
    positive_pairs = pairs[pairs >= 0]
    
    print(f"Top {n} lowest positive correlated pairs:\n")
    for (ticker1, ticker2), corr in positive_pairs.head(n).items():
        print(f"{ticker1} vs {ticker2}: {corr:.4f}")
    
    return positive_pairs.head(n)

lowest_pairs = get_lowest_correlations(corr_matrix, n=10)

#Now want to check dividend info to maximize returns
def get_dividend_info(tickers):
    """Get dividend yield and info for a list of tickers."""
    dividend_data = []
    
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            dividend_data.append({
                'ticker': ticker,
                'dividend_yield': info.get('dividendYield', 0) or 0,
                'dividend_rate': info.get('dividendRate', 0) or 0,
                'payout_ratio': info.get('payoutRatio', 0) or 0,
                'sector': info.get('sector', 'Unknown'),
                'name': info.get('shortName', ticker)
            })
        except Exception as e:
            print(f"  Error fetching {ticker}: {e}")
            dividend_data.append({
                'ticker': ticker,
                'dividend_yield': 0,
                'dividend_rate': 0,
                'payout_ratio': 0,
                'sector': 'Unknown',
                'name': ticker
            })
    
    df = pd.DataFrame(dividend_data)
    df['dividend_yield_pct'] = df['dividend_yield'] * 100
    df = df.sort_values('dividend_yield', ascending=False)
    
    return df

# Extract unique tickers from pairs
uncorrelated_tickers = list({t for pair in lowest_pairs.index for t in pair})

print("Fetching dividend data for uncorrelated stocks...")
uncorr_dividends = get_dividend_info(uncorrelated_tickers)
print("\nUncorrelated stocks by dividend yield:")
print(uncorr_dividends[['ticker', 'name', 'dividend_yield_pct', 'dividend_rate', 'sector']].to_string(index=False))


#now use XGBoost for predicting future returns based on features like past correlations, momentum, div yield, volatility, etc.
def create_feature_dataset(prices, lookback_months=6, forward_months=3):
    """
    Create a feature dataset for ML from price data.
    
    Each row = one stock at one point in time
    Features = what we know at that time
    Target = future return (what we're predicting)
    """
    
    # Calculate daily returns
    returns = prices.pct_change()

    # We'll build features at monthly intervals
    # Get month-end dates
    monthly_dates = prices.resample('M').last().index

    # Need enough history for lookback and enough future for target
    valid_dates = monthly_dates[lookback_months:-forward_months]

    all_rows = []

    for date in valid_dates:
        print(f"Processing {date.strftime('%Y-%m')}...")

        # Get lookback window
        lookback_start = date - pd.DateOffset(months=lookback_months)
        lookback_returns = returns[lookback_start:date]

        # Get forward window (for target)
        forward_end = date + pd.DateOffset(months=forward_months)
        forward_returns = returns[date:forward_end]

        # Calculate correlation matrix for this period
        corr_matrix = lookback_returns.corr()

        # Market proxy (equal-weighted average of all stocks)
        market_return = lookback_returns.mean(axis=1)

        for ticker in prices.columns:
            try:
                ticker_returns = lookback_returns[ticker].dropna()

                if len(ticker_returns) < 20:  # Skip if not enough data
                    continue

                # === FEATURES ===

                # 1. Momentum (past return over lookback period)
                momentum = (prices[ticker].loc[:date].iloc[-1] / 
                           prices[ticker].loc[:date].iloc[-lookback_months*21] - 1)

                # 2. Volatility (std of daily returns)
                volatility = ticker_returns.std() * np.sqrt(252)  # Annualized

                # 3. Average correlation with all other stocks
                ticker_corrs = corr_matrix[ticker].drop(ticker)
                avg_correlation = ticker_corrs.mean()

                # 4. Max correlation (how tied to another stock)
                max_correlation = ticker_corrs.max()

                # 5. Min correlation (most diversifying pair)
                min_correlation = ticker_corrs.min()

                # 6. Correlation with "market" (equal-weight avg)
                market_corr = ticker_returns.corr(market_return)

                # 7. Sharpe ratio (return / volatility)
                period_return = ticker_returns.sum()
                sharpe = period_return / (ticker_returns.std() + 1e-6)

                # 8. Recent vs older momentum (trend acceleration)
                recent_return = ticker_returns.iloc[-21:].sum()  # Last month
                older_return = ticker_returns.iloc[:-21].sum()   # Before that
                momentum_accel = recent_return - older_return

                # === TARGET ===
                # Future return over forward_months
                if ticker in forward_returns.columns:
                    future_return = forward_returns[ticker].sum()
                else:
                    continue

                # Did it beat the market?
                market_future = forward_returns.mean(axis=1).sum()
                beat_market = 1 if future_return > market_future else 0

                all_rows.append({
                    'ticker': ticker,
                    'date': date,
                    'momentum': momentum,
                    'volatility': volatility,
                    'avg_correlation': avg_correlation,
                    'max_correlation': max_correlation,
                    'min_correlation': min_correlation,
                    'market_correlation': market_corr,
                    'sharpe': sharpe,
                    'momentum_accel': momentum_accel,
                    'future_return': future_return,
                    'beat_market': beat_market
                })

            except Exception as e:
                continue

    return pd.DataFrame(all_rows)


def add_dividend_features(df, tickers):
    """Add dividend yield as a feature."""
    print("Fetching dividend data...")
    
    div_yields = {}
    for i, ticker in enumerate(tickers):
        if i % 100 == 0:
            print(f"  Progress: {i}/{len(tickers)}")
        try:
            stock = yf.Ticker(ticker)
            div_yields[ticker] = stock.info.get('dividendYield', 0) or 0
        except:
            div_yields[ticker] = 0
    
    df['dividend_yield'] = df['ticker'].map(div_yields)
    return df


# === RUN IT ===

# Assuming you have 'prices' from your earlier download
print("Creating feature dataset...")
feature_df = create_feature_dataset(prices, lookback_months=6, forward_months=3)

print(f"\nDataset shape: {feature_df.shape}")
print(f"Date range: {feature_df['date'].min()} to {feature_df['date'].max()}")
print(f"\nSample rows:")
print(feature_df.head(10))

# Add dividend data
unique_tickers = feature_df['ticker'].unique()
feature_df = add_dividend_features(feature_df, unique_tickers)

# Save it so you don't have to rebuild
feature_df.to_csv('stock_features.csv', index=False)
print("\nSaved to stock_features.csv")