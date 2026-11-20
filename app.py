import streamlit as st             # builds the web app
import yfinance as yf              # downloads stock data
import pandas as pd                # tables and data handling
import plotly.graph_objects as go  # makes interactive charts
from plotly.subplots import make_subplots  # stacks charts vertically

st.title("MarketScope")

# One time-period dropdown shared by all tabs
period = st.selectbox("Time period", ["6mo", "1y", "5y", "10y"], index=1)

tab1, tab2, tab3 = st.tabs(["Explorer", "Compare", "Portfolio"])

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
    tickers = [t.strip().upper() for t in raw.split(",") if t.strip()][:4]

    if len(tickers) < 2:
        st.info("Enter at least two tickers.")
    else:
        prices = yf.download(
            tickers, period=period, auto_adjust=True, progress=False
        )["Close"]
        if isinstance(prices, pd.Series):
            prices = prices.to_frame(name=tickers[0])
        prices = prices.dropna()

        if prices.empty:
            st.error("No data found. Check the ticker symbols.")
        else:
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

            daily = prices.pct_change().dropna()
            summary = pd.DataFrame({
                "Total return (%)": prices.iloc[-1] / prices.iloc[0] - 1,
                "Annualized volatility (%)": daily.std() * (252 ** 0.5),
            })
            st.dataframe((summary * 100).round(1))

# ---------------- TAB 3: portfolio ----------------
with tab3:
    raw_p = st.text_input(
        "Holdings as TICKER:SHARES, separated by commas",
        value="AAPL:10, MSFT:5, NVDA:8, KO:15",
    )
    rf = st.number_input("Risk-free rate (%)", value=4.0, step=0.25) / 100

    # Turn the text into a dictionary like {"AAPL": 10.0, "MSFT": 5.0}
    holdings = {}
    try:
        for item in raw_p.split(","):
            if item.strip():
                t, s = item.split(":")
                holdings[t.strip().upper()] = float(s)
    except ValueError:
        st.error("Use the format AAPL:10, MSFT:5")
        holdings = {}

    if holdings:
        names = list(holdings.keys())
        bench = "SPY"  # S&P 500 ETF, used as the benchmark
        all_names = list(dict.fromkeys(names + [bench]))

        px = yf.download(
            all_names, period=period, auto_adjust=True, progress=False
        )["Close"]
        if isinstance(px, pd.Series):
            px = px.to_frame(name=all_names[0])
        px = px.dropna(axis=1, how="all").dropna()

        missing = [n for n in all_names if n not in px.columns]
        if missing or px.empty:
            st.error(f"No data for: {', '.join(missing) or 'these tickers'}")
        else:
            shares = pd.Series(holdings)
            values = px[names] * shares        # dollar value of each holding
            port = values.sum(axis=1)          # total portfolio value per day

            # Risk and return metrics
            r = port.pct_change().dropna()
            total_ret = port.iloc[-1] / port.iloc[0] - 1
            vol = r.std() * (252 ** 0.5)
            sharpe = (r.mean() * 252 - rf) / vol
            drawdown = port / port.cummax() - 1
            max_dd = drawdown.min()

            c1, c2, c3 = st.columns(3)
            c1.metric("Current value", f"${port.iloc[-1]:,.0f}")
            c2.metric("Total return", f"{total_ret:.1%}")
            c3.metric("Annualized volatility", f"{vol:.1%}")
            c4, c5 = st.columns(2)
            c4.metric("Sharpe ratio", f"{sharpe:.2f}")
            c5.metric("Max drawdown", f"{max_dd:.1%}")

            # Portfolio vs S&P 500, both rebased to 100
            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(
                x=port.index, y=port / port.iloc[0] * 100, name="Portfolio"
            ))
            fig3.add_trace(go.Scatter(
                x=px.index, y=px[bench] / px[bench].iloc[0] * 100,
                name="S&P 500 (SPY)"
            ))
            fig3.update_layout(
                yaxis_title="Growth of 100 invested", height=400
            )
            st.plotly_chart(fig3, width="stretch")

            # Allocation pie chart
            latest = values.iloc[-1]
            fig4 = go.Figure(go.Pie(
                labels=latest.index, values=latest.values, hole=0.4
            ))
            fig4.update_layout(title="Allocation by current value", height=400)
            st.plotly_chart(fig4, width="stretch")

            st.caption(
                "Assumes you held these share counts for the whole period. "
                "Sharpe = (annualized return - risk-free rate) / volatility. "
                "Educational only, not investment advice."
            )