# MarketScope

A stock market analytics dashboard built with Python and Streamlit.

**Status:** In development
**Live demo:** https://marketscope.streamlit.app

## Features so far

- Interactive candlestick chart for any ticker
- 50-day moving average, volume, and RSI panels
- Total return and annualized volatility over a selectable period
- Side-by-side comparison of 2-4 tickers
- Portfolio tab: value, allocation, and performance vs. the S&P 500
- Risk metrics: Sharpe ratio, max drawdown, beta, alpha, and 1-day 95% VaR (historical and parametric)
- Correlation heatmap of holdings
- Efficient frontier optimizer (Markowitz mean-variance) with max-Sharpe and min-volatility portfolios
- Monte Carlo simulation of portfolio outcomes (1-5 year horizon) with percentile bands and probability of loss
- DCF calculator with editable assumptions and a WACC / terminal growth sensitivity table

## Planned features

- MACD and Bollinger Bands
- Stress tests (2008, 2020, 2022)

## Tech stack

Python, Streamlit, pandas, NumPy, SciPy, Plotly, yfinance

## Run it locally

    git clone https://github.com/andremorero1-bit/marketscope.git
    cd marketscope
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    streamlit run app.py

## Disclaimer

For educational purposes only. Not investment advice.