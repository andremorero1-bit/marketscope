# MarketScope

A stock market analytics dashboard built with Python and Streamlit.

**Status:** In development

## Features so far

- Interactive candlestick chart for any ticker
- 50-day moving average, volume, and RSI panels
- Total return and annualized volatility over a selectable period
- Side-by-side comparison of 2-4 tickers

## Planned features

- MACD and Bollinger Bands
- Portfolio builder with performance and risk metrics (Sharpe, beta, VaR)
- Efficient frontier optimizer and Monte Carlo simulation

## Tech stack

Python, Streamlit, pandas, Plotly, yfinance

## Run it locally

    git clone https://github.com/andremorero1-bit/marketscope.git
    cd marketscope
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    streamlit run app.py

## Disclaimer

For educational purposes only. Not investment advice.