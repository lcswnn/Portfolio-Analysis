"""
Print stock recommendations to the terminal, matching the website's groupings.
Run from the backend/ directory: python print_recommendations.py
"""

import os
import sys
import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
import stock_data_generator as sdg

script_dir = os.path.dirname(os.path.abspath(__file__))

# ── Load & train ──────────────────────────────────────────────────────────────

df = pd.read_csv(os.path.join(script_dir, 'stock_features.csv'))
df['date'] = pd.to_datetime(df['date'])
df = df.replace([np.inf, -np.inf], np.nan).dropna()

feature_cols = [
    'momentum', 'volatility', 'avg_correlation', 'max_correlation',
    'min_correlation', 'market_correlation', 'sharpe', 'momentum_accel',
    'dividend_yield'
]

print("Training model...")
model = CatBoostClassifier(iterations=200, depth=4, learning_rate=0.05, random_state=42, verbose=False)
model.fit(df[feature_cols], df['beat_market'])

# ── Load latest features ──────────────────────────────────────────────────────
# By default this ALWAYS pulls a fresh price snapshot as of right now (today's
# most recent trading data), because stock_features.csv's newest usable row is
# always ~3 months stale (it needs 3 future months of returns to label
# 'beat_market' during training, so recent months get trimmed out).
#
# Pass --cached to skip the refresh and reuse the existing latest_features.csv
# (faster, but only as fresh as the last time you ran without --cached).

latest_path = os.path.join(script_dir, 'latest_features.csv')
use_cached = '--cached' in sys.argv

if use_cached and os.path.exists(latest_path):
    print(f"Using cached {latest_path} (drop --cached to pull fresh data)...")
    latest = pd.read_csv(latest_path)
    latest['date'] = pd.to_datetime(latest['date'])
    data_source = "CACHED"
else:
    print("Pulling live price data as of right now...")
    latest = sdg.fetch_latest_features(output_path=latest_path)
    data_source = "LIVE"

latest['date'] = pd.to_datetime(latest['date'])
latest = latest.replace([np.inf, -np.inf], np.nan).dropna()

latest['prob_beat_market'] = model.predict_proba(latest[feature_cols])[:, 1]
latest_date = latest['date'].max()

# ── Helpers ───────────────────────────────────────────────────────────────────

W = 95

def header(title):
    print(f"\n{'='*W}")
    print(f"  {title}")
    print(f"{'='*W}")

def row(rank, r, extra_col=None, extra_label=""):
    base = (f"  {rank:<4} {r['ticker']:<8} "
            f"Prob: {r['prob_beat_market']*100:>5.1f}%  "
            f"Sharpe: {r['sharpe']:>6.2f}  "
            f"Momentum: {r['momentum']*100:>6.1f}%  "
            f"Vol: {r['volatility']*100:>5.1f}%  "
            f"Div: {r['dividend_yield']*100:>5.2f}%")
    if extra_col is not None:
        base += f"  {extra_label}: {extra_col:>6.3f}"
    print(base)

def col_header(extra=""):
    print(f"  {'#':<4} {'Ticker':<8} {'Prob':>9}  {'Sharpe':>12}  {'Momentum':>14}  {'Vol':>10}  {'Div':>10}" + (f"  {extra}" if extra else ""))
    print(f"  {'-'*W}")

# ── Summary stats ─────────────────────────────────────────────────────────────

header("SUMMARY")
print(f"  Data source   : {data_source}")
print(f"  As of         : {latest_date.strftime('%Y-%m-%d')}")
print(f"  Total analyzed: {len(latest)}")
print(f"  Above 50%     : {len(latest[latest['prob_beat_market'] > 0.50])}")
print(f"  Above 55%     : {len(latest[latest['prob_beat_market'] > 0.55])}")
print(f"  Above 60%     : {len(latest[latest['prob_beat_market'] > 0.60])}")
print(f"  Avg prob      : {latest['prob_beat_market'].mean()*100:.1f}%")
print(f"  Max prob      : {latest['prob_beat_market'].max()*100:.1f}%")

# ── Top 5 composite picks ─────────────────────────────────────────────────────

sc = latest.copy()
for col, mn, mx in [
    ('norm_prob',      'prob_beat_market', None),
    ('norm_sharpe',    'sharpe',           None),
    ('norm_stability', 'volatility',       None),
    ('norm_momentum',  'momentum',         None),
]:
    src = mn
    q_min = sc[src].quantile(0.05)
    q_max = sc[src].quantile(0.95)
    clipped = sc[src].clip(q_min, q_max)
    normalized = (clipped - q_min) / (q_max - q_min + 1e-6)
    if col == 'norm_stability':
        normalized = 1 - normalized
    sc[col] = normalized

sc['composite_score'] = (
    0.40 * sc['norm_prob'] +
    0.25 * sc['norm_sharpe'] +
    0.20 * sc['norm_stability'] +
    0.15 * sc['norm_momentum']
)

top5 = sc.nlargest(5, 'composite_score')

header("TOP 5 PICKS  (40% Prob · 25% Sharpe · 20% Stability · 15% Momentum)")
col_header("Score")
for i, (_, r) in enumerate(top5.iterrows(), 1):
    row(i, r, extra_col=r['composite_score'], extra_label="Score")

# ── Top 20 by probability ─────────────────────────────────────────────────────

top20 = latest[latest['prob_beat_market'] >= 0.5].sort_values('prob_beat_market', ascending=False).head(20)

header("TOP 20 — Highest Probability (≥50%)")
col_header()
for i, (_, r) in enumerate(top20.iterrows(), 1):
    row(i, r)

# ── Curated: Best Overall ─────────────────────────────────────────────────────

candidates = latest[latest['prob_beat_market'] >= 0.5].copy()

best_overall = candidates[candidates['sharpe'] > 0].sort_values('prob_beat_market', ascending=False).head(5)

header("CURATED — Best Overall  (prob ≥50% + positive Sharpe)")
col_header()
for i, (_, r) in enumerate(best_overall.iterrows(), 1):
    row(i, r)

# ── Curated: Income Focused ───────────────────────────────────────────────────

income = candidates[candidates['dividend_yield'] >= 0.01].sort_values(
    ['dividend_yield', 'prob_beat_market'], ascending=[False, False]
).head(5)

header("CURATED — Income Focused  (prob ≥50% + dividend ≥1%)")
col_header()
for i, (_, r) in enumerate(income.iterrows(), 1):
    row(i, r)

# ── Curated: Low Risk ─────────────────────────────────────────────────────────

low_risk = candidates[candidates['volatility'] < 0.5].sort_values(
    ['volatility', 'prob_beat_market'], ascending=[True, False]
).head(5)

header("CURATED — Low Risk  (prob ≥50% + volatility <50%)")
col_header()
for i, (_, r) in enumerate(low_risk.iterrows(), 1):
    row(i, r)

print(f"\n{'='*W}\n")