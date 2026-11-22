import streamlit as st             # builds the web app
import yfinance as yf              # downloads stock data
import pandas as pd                # tables and data handling
import plotly.graph_objects as go  # makes interactive charts
from plotly.subplots import make_subplots  # stacks charts vertically

st.title("MarketScope")

# One time-period dropdown shared by all tabs
period = st.selectbox("Time period", ["6mo", "1y", "5y", "10y"], index=1)

tab1, tab2, tab3, tab4 = st.tabs(["Explorer", "Compare", "Portfolio", "Optimizer"])

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
                "Sharpe = (annualized return - risk-free rate)"
                " / volatility. "
                "Educational only, not investment advice."
            )
            # ---------- Beta, alpha, and Value at Risk ----------
            bench_r = px[bench].pct_change().dropna()
            aligned = pd.concat([r, bench_r], axis=1, join="inner").dropna()
            aligned.columns = ["port", "bench"]

            # Beta = covariance(portfolio, market) / variance(market)
            beta = aligned["port"].cov(aligned["bench"]) / aligned["bench"].var()
            # Alpha (annualized) = portfolio return - [rf + beta * (market return - rf)]
            alpha = (aligned["port"].mean() * 252 - rf) - beta * (
                aligned["bench"].mean() * 252 - rf
            )

            # 95% one-day VaR, as a loss on today's portfolio value
            hist_var = -r.quantile(0.05)
            param_var = -(r.mean() - 1.645 * r.std())
            current_val = port.iloc[-1]

            st.subheader("Market risk")
            m1, m2 = st.columns(2)
            m1.metric("Beta vs S&P 500", f"{beta:.2f}")
            m2.metric("Alpha (annualized)", f"{alpha:.1%}")
            v1, v2 = st.columns(2)
            v1.metric(
                "1-day VaR 95% (historical)",
                f"${hist_var * current_val:,.0f}",
                f"{hist_var:.2%} of portfolio", delta_color="off",
            )
            v2.metric(
                "1-day VaR 95% (parametric)",
                f"${param_var * current_val:,.0f}",
                f"{param_var:.2%} of portfolio", delta_color="off",
            )

            # ---------- Correlation heatmap ----------
            if len(names) >= 2:
                corr = px[names].pct_change().dropna().corr()
                fig5 = go.Figure(go.Heatmap(
                    z=corr.values, x=corr.columns, y=corr.index,
                    zmin=-1, zmax=1, colorscale="RdBu_r",
                    text=corr.round(2).values, texttemplate="%{text}",
                ))
                fig5.update_layout(
                    title="Correlation of daily returns", height=450
                )
                st.plotly_chart(fig5, width="stretch")

            st.caption(
                "VaR is a statistical estimate, not a guarantee: real losses "
                "can exceed it, especially in market crashes. Beta and alpha "
                "are measured against SPY over the selected period."
            )

           
# ---------------- TAB 4: efficient frontier optimizer ----------------
import numpy as np
from scipy.optimize import minimize

with tab4:
    raw_o = st.text_input(
        "Tickers to optimize (2-10), separated by commas",
        value="AAPL, MSFT, NVDA, KO, JPM", key="opt_tickers",
    )
    rf_o = st.number_input(
        "Risk-free rate (%)", value=4.0, step=0.25, key="opt_rf"
    ) / 100
    st.caption("Tip: use the 5y or 10y period above. 6 months is too little data.")

    tick_o = list(dict.fromkeys(
        t.strip().upper() for t in raw_o.split(",") if t.strip()
    ))[:10]

    if len(tick_o) < 2:
        st.info("Enter at least two tickers.")
    else:
        px_o = yf.download(
            tick_o, period=period, auto_adjust=True, progress=False
        )["Close"]
        if isinstance(px_o, pd.Series):
            px_o = px_o.to_frame(name=tick_o[0])
        px_o = px_o.dropna(axis=1, how="all").dropna()

        if px_o.shape[1] < 2 or len(px_o) < 60:
            st.error("Not enough data. Check the tickers or use a longer period.")
        else:
            rets = px_o.pct_change().dropna()
            names_o = list(px_o.columns)
            mu = rets.mean().values * 252      # expected annual returns
            cov = rets.cov().values * 252      # annual covariance matrix
            n = len(mu)

            def stats(w):
                return w @ mu, np.sqrt(w @ cov @ w)   # (return, volatility)

            sum_to_one = {"type": "eq", "fun": lambda w: w.sum() - 1}
            bounds = [(0, 1)] * n                      # long-only
            w0 = np.ones(n) / n

            # Max Sharpe and minimum volatility portfolios
            ms = minimize(
                lambda w: -(stats(w)[0] - rf_o) / stats(w)[1],
                w0, method="SLSQP", bounds=bounds, constraints=[sum_to_one],
            )
            mv = minimize(
                lambda w: stats(w)[1],
                w0, method="SLSQP", bounds=bounds, constraints=[sum_to_one],
            )
            w_ms, w_mv = ms.x, mv.x

            # Efficient frontier: lowest volatility for each target return
            f_vol, f_ret = [], []
            for t in np.linspace(stats(w_mv)[0], mu.max(), 30):
                res = minimize(
                    lambda w: stats(w)[1], w0, method="SLSQP", bounds=bounds,
                    constraints=[sum_to_one,
                                 {"type": "eq", "fun": lambda w, t=t: w @ mu - t}],
                )
                if res.success:
                    f_vol.append(stats(res.x)[1])
                    f_ret.append(t)

            # 4,000 random portfolios for the background cloud
            rng = np.random.default_rng(42)
            W = rng.dirichlet(np.ones(n), 4000)
            R = W @ mu
            V = np.sqrt(np.einsum("ij,jk,ik->i", W, cov, W))
            S = (R - rf_o) / V

            fig6 = go.Figure()
            fig6.add_trace(go.Scatter(
                x=V, y=R, mode="markers", name="Random portfolios",
                marker=dict(color=S, colorscale="Viridis", size=5,
                            colorbar=dict(title="Sharpe")),
            ))
            fig6.add_trace(go.Scatter(
                x=f_vol, y=f_ret, mode="lines", name="Efficient frontier",
                line=dict(width=3),
            ))
            for label, w in [("Max Sharpe", w_ms), ("Min volatility", w_mv)]:
                ret, vol = stats(w)
                fig6.add_trace(go.Scatter(
                    x=[vol], y=[ret], mode="markers", name=label,
                    marker=dict(size=16, symbol="star",
                                line=dict(width=1, color="black")),
                ))
            fig6.update_layout(
                xaxis_title="Annualized volatility",
                yaxis_title="Annualized return",
                xaxis_tickformat=".0%", yaxis_tickformat=".0%", height=500,
            )
            st.plotly_chart(fig6, width="stretch")

            # Weights and summary table
            weights = pd.DataFrame(
                {"Max Sharpe": w_ms, "Min volatility": w_mv}, index=names_o
            )
            st.subheader("Optimal weights (%)")
            st.dataframe((weights * 100).round(1))

            summary_o = pd.DataFrame({
                label: {
                    "Expected return": stats(w)[0],
                    "Volatility": stats(w)[1],
                    "Sharpe ratio": (stats(w)[0] - rf_o) / stats(w)[1],
                }
                for label, w in [("Max Sharpe", w_ms), ("Min volatility", w_mv)]
            })
            st.dataframe(summary_o.round(3))

            st.caption(
                "Mean-variance optimization (Markowitz), long-only. Expected "
                "returns are estimated from past data, which is noisy, so "
                "results are in-sample and not a forecast. Educational only, "
                "not investment advice."
            ) 