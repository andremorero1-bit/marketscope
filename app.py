import streamlit as st             # builds the web app
import yfinance as yf              # downloads stock data
import plotly.graph_objects as go  # makes interactive charts

st.title("MarketScope")

# A text box where the user types a ticker symbol
ticker = st.text_input("Enter a ticker", value="AAPL").upper()

# A dropdown for how far back to look
period = st.selectbox("Time period", ["6mo", "1y", "5y"], index=1)

# Download price history. This returns a "DataFrame" (a table).
data = yf.Ticker(ticker).history(period=period)

if data.empty:
    st.error("No data found. Check the ticker symbol.")
else:
    # Add a 50-day moving average column to the table
    data["MA50"] = data["Close"].rolling(window=50).mean()

    # Daily returns: % change in closing price day to day
    data["Return"] = data["Close"].pct_change()

    # Total return over the whole period
    total_return = data["Close"].iloc[-1] / data["Close"].iloc[0] - 1

    # Annualized volatility: daily std dev scaled by sqrt(252 trading days)
    volatility = data["Return"].std() * (252 ** 0.5)

    # Show the two numbers as metric cards
    col1, col2 = st.columns(2)
    col1.metric("Total return", f"{total_return:.1%}")
    col2.metric("Annualized volatility", f"{volatility:.1%}")

    # Build a candlestick chart
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data["Open"], high=data["High"],
        low=data["Low"], close=data["Close"],
        name="Price"
    ))
    fig.add_trace(go.Scatter(x=data.index, y=data["MA50"], name="50-day MA"))
    st.plotly_chart(fig, width="stretch")

    # Show the last few rows of raw data
    st.dataframe(data.tail())