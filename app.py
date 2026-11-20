import streamlit as st             # builds the web app
import yfinance as yf              # downloads stock data
import pandas as pd                # tables and data handling
import plotly.graph_objects as go  # makes interactive charts
from plotly.subplots import make_subplots  # stacks charts vertically

st.title("MarketScope")

# One time-period dropdown shared by both tabs
period = st.selectbox("Time period", ["6mo", "1y", "5y", "10y"], index=1)

tab1, tab2 = st.tabs(["Explorer", "Compare"])

# ---------------- TAB 1: single-stock explorer ----------------
with tab1:
    ticker = st.text_input("Enter a ticker", value="AAPL").upper()
    data = yf.Ticker(ticker).history(period=period)

    if data.empty:
        st.error("No data found. Check the ticker symbol.")
    else:
        data["MA50"] = data["Close"].rolling(window=50).mean()
        data["Return"] = data["Close"].pct_change()

        total_return = data["Close"].iloc[-1] / data["Close"].iloc[0] - 1
        volatility = data["Return"].std() * (252 ** 0.5)

        # RSI (14-day)
        delta = data["Close"].diff()
        gain = delta.clip(lower=0).rolling(window=14).mean()
        loss = (-delta.clip(upper=0)).rolling(window=14).mean()
        data["RSI"] = 100 - (100 / (1 + gain / loss))

        col1, col2 = st.columns(2)
        col1.metric("Total return", f"{total_return:.1%}")
        col2.metric("Annualized volatility", f"{volatility:.1%}")

        fig = make_subplots(
            rows=3, cols=1, shared_xaxes=True,
            row_heights=[0.6, 0.2, 0.2], vertical_spacing=0.03,
        )
        fig.add_trace(go.Candlestick(
            x=data.index,
            open=data["Open"], high=data["High"],
            low=data["Low"], close=data["Close"],
            name="Price"
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=data.index, y=data["MA50"], name="50-day MA"
        ), row=1, col=1)
        fig.add_trace(go.Bar(
            x=data.index, y=data["Volume"], name="Volume"
        ), row=2, col=1)
        fig.add_trace(go.Scatter(
            x=data.index, y=data["RSI"], name="RSI"
        ), row=3, col=1)
        fig.add_hline(y=70, line_dash="dash", row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", row=3, col=1)
        fig.update_layout(xaxis_rangeslider_visible=False, height=750)
        st.plotly_chart(fig, width="stretch")

        st.dataframe(data.tail())

# ---------------- TAB 2: compare several stocks ----------------
with tab2:
    raw = st.text_input(
        "Enter 2-4 tickers, separated by commas", value="AAPL, MSFT, NVDA"
    )
    # Turn the text into a clean list like ["AAPL", "MSFT", "NVDA"]
    tickers = [t.strip().upper() for t in raw.split(",") if t.strip()][:4]

    if len(tickers) < 2:
        st.info("Enter at least two tickers.")
    else:
        prices = yf.download(
            tickers, period=period, auto_adjust=True, progress=False
        )["Close"]
        if isinstance(prices, pd.Series):  # safety net if only one came back
            prices = prices.to_frame(name=tickers[0])
        prices = prices.dropna()

        if prices.empty:
            st.error("No data found. Check the ticker symbols.")
        else:
            # Rebase every stock to 100 on day one so they're comparable
            growth = prices / prices.iloc[0] * 100

            fig2 = go.Figure()
            for name in growth.columns:
                fig2.add_trace(go.Scatter(
                    x=growth.index, y=growth[name], name=name
                ))
            fig2.update_layout(
                yaxis_title="Growth of 100 invested", height=450
            )
            st.plotly_chart(fig2, width="stretch")

            # Summary table: total return and volatility for each stock
            daily = prices.pct_change().dropna()
            summary = pd.DataFrame({
                "Total return (%)": prices.iloc[-1] / prices.iloc[0] - 1,
                "Annualized volatility (%)": daily.std() * (252 ** 0.5),
            })
            st.dataframe((summary * 100).round(1))