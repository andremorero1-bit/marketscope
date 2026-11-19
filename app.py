import streamlit as st             # builds the web app
import yfinance as yf              # downloads stock data
import plotly.graph_objects as go  # makes interactive charts
from plotly.subplots import make_subplots  # stacks charts vertically

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

    # RSI (14-day): compares average gains to average losses
    delta = data["Close"].diff()
    gain = delta.clip(lower=0).rolling(window=14).mean()
    loss = (-delta.clip(upper=0)).rolling(window=14).mean()
    data["RSI"] = 100 - (100 / (1 + gain / loss))

    # Show the two numbers as metric cards
    col1, col2 = st.columns(2)
    col1.metric("Total return", f"{total_return:.1%}")
    col2.metric("Annualized volatility", f"{volatility:.1%}")

    # Build a chart with 3 stacked panels: price, volume, RSI
    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True,
        row_heights=[0.6, 0.2, 0.2], vertical_spacing=0.03,
    )

    # Panel 1: candlesticks and moving average
    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data["Open"], high=data["High"],
        low=data["Low"], close=data["Close"],
        name="Price"
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=data.index, y=data["MA50"], name="50-day MA"
    ), row=1, col=1)

    # Panel 2: volume bars
    fig.add_trace(go.Bar(
        x=data.index, y=data["Volume"], name="Volume"
    ), row=2, col=1)

    # Panel 3: RSI with the 70 and 30 reference lines
    fig.add_trace(go.Scatter(
        x=data.index, y=data["RSI"], name="RSI"
    ), row=3, col=1)
    fig.add_hline(y=70, line_dash="dash", row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", row=3, col=1)

    # Hide the range slider so the panels stay clean, and set the height
    fig.update_layout(xaxis_rangeslider_visible=False, height=750)

    st.plotly_chart(fig, width="stretch")

    # Show the last few rows of raw data
    st.dataframe(data.tail())