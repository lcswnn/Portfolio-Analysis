"""
Stock data generation module - handles downloading and feature engineering for stock data.
Can be used both as a CLI script and imported by Flask app for API endpoints.
"""

import re
import json
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import time


def fetch_etf_holdings(url, headers):
    """Fetch ETF holdings from Zacks website."""
    try:
        data = requests.get(url, headers=headers, timeout=10)
        html_content = data.text

        # Extract JavaScript data
        pattern = r'etf_holdings\.formatted_data\s*=\s*(\[.*?\]);'
        match = re.search(pattern, html_content, re.DOTALL)

        if match:
            data_str = match.group(1)
            holdings_data = json.loads(data_str)
            symbol_list = []

            for row in holdings_data:
                symbol_html = row[1]
                symbol_soup = BeautifulSoup(symbol_html, 'html.parser')
                symbol_span = symbol_soup.find('span', class_='hoverquote-symbol')
                if symbol_span:
                    symbol_list.append(symbol_span.get_text(strip=True))
                else:
                    symbol_list.append(row[1].strip())

            return symbol_list
        return []
    except Exception as e:
        print(f"Error fetching ETF holdings: {e}")
        return []


def get_all_tickers():
    """Fetch all ticker symbols from large, mid, and small cap ETFs."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    large_cap_url = 'https://www.zacks.com/funds/etf/SPY/holding'
    mid_cap_url = 'https://www.zacks.com/funds/etf/MDY/holding'
    small_cap_url = 'https://www.zacks.com/funds/etf/SPSM/holding'

    print("Fetching ETF holdings...")
    large_symbol_list = fetch_etf_holdings(large_cap_url, headers)
    mid_symbol_list = fetch_etf_holdings(mid_cap_url, headers)
    small_symbol_list = fetch_etf_holdings(small_cap_url, headers)

    print(f"Found {len(large_symbol_list)} large cap symbols")
    print(f"Found {len(mid_symbol_list)} mid cap symbols")
    print(f"Found {len(small_symbol_list)} small cap symbols")

    return large_symbol_list, mid_symbol_list, small_symbol_list


def is_valid_ticker(ticker):
    """Filter out invalid ticker symbols."""
    pattern = r'^[A-Z]{1,5}(\.[A-Z])?$'
    return bool(re.match(pattern, ticker))


def filter_tickers(large_list, mid_list, small_list):
    """Filter and deduplicate ticker list."""
    all_tickers = large_list + mid_list + small_list
    all_tickers = list(set(all_tickers))
    print(f"Total unique tickers: {len(all_tickers)}")

    valid_tickers = [t for t in all_tickers if is_valid_ticker(t)]
    invalid_tickers = [t for t in all_tickers if not is_valid_ticker(t)]

    # Add US Cash Index
    valid_tickers.append('DX-Y.NYB')

    print(f"Valid tickers: {len(valid_tickers)}")
    print(f"Filtered out: {len(invalid_tickers)} invalid tickers")

    return valid_tickers


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


def generate_stock_features(output_path='stock_features.csv'):
    """
    Main function to generate stock features CSV file.
    Downloads fresh data from yfinance and creates ML features.

    Args:
        output_path: Path where to save the stock_features.csv file

    Returns:
        DataFrame with stock features, or None if failed
    """
    try:
        print("=" * 60)
        print("Starting stock data generation...")
        print("=" * 60)

        # Step 1: Fetch tickers
        large_list, mid_list, small_list = get_all_tickers()
        valid_tickers = filter_tickers(large_list, mid_list, small_list)

        # Step 2: Download price data
        print("\nDownloading price data (this may take a while)...")
        prices = download_in_batches(valid_tickers, period='5y', interval='1d', batch_size=30, delay=2)

        # Filter out bad data
        prices = prices.dropna(axis=1, how='all')
        min_data_points = 250
        prices = prices.dropna(axis=1, thresh=min_data_points)
        print(f"Valid tickers remaining: {len(prices.columns)}")

        # Step 3: Create features
        print("\nCreating feature dataset...")
        feature_df = create_feature_dataset(prices, lookback_months=6, forward_months=3)
        print(f"Feature dataset shape: {feature_df.shape}")
        print(f"Date range: {feature_df['date'].min()} to {feature_df['date'].max()}")

        # Step 4: Add dividend data
        unique_tickers = feature_df['ticker'].unique()
        feature_df = add_dividend_features(feature_df, unique_tickers)

        # Step 5: Save to CSV
        feature_df.to_csv(output_path, index=False)
        print(f"\nSuccessfully saved to {output_path}")
        print(f"Total rows: {len(feature_df)}")
        print(f"Date range: {feature_df['date'].min()} to {feature_df['date'].max()}")

        return feature_df

    except Exception as e:
        print(f"Error generating stock features: {e}")
        raise


if __name__ == '__main__':
    # CLI usage
    import sys
    output_path = sys.argv[1] if len(sys.argv) > 1 else 'stock_features.csv'
    generate_stock_features(output_path)
