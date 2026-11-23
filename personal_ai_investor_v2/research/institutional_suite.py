"""Free-data institutional research workspaces.

Uses Yahoo Finance through the existing app adapter for price/quote data.
Investopedia and other publishers are linked as education/research references, not scraped.
SEC EDGAR is used only when the operator supplies a compliant SEC_USER_AGENT contact string.
"""
import os
import numpy as np
import pandas as pd
import streamlit as st

from data.market_data import history, info

EDUCATION = {
    "Investopedia": ("https://www.investopedia.com/", "Financial concepts, ratios and investing education"),
    "Bogleheads": ("https://www.bogleheads.org/wiki/Main_Page", "Low-cost indexing, diversification and long-term discipline"),
    "Mr. Money Mustache": ("https://www.mrmoneymustache.com/", "Financial independence and savings-rate thinking"),
    "The Balance": ("https://www.thebalancemoney.com/", "Plain-English personal finance education"),
    "Wall Street Mojo": ("https://www.wallstreetmojo.com/", "Accounting, valuation and financial-modeling explainers"),
    "Early Retirement Now": ("https://earlyretirementnow.com/", "Detailed retirement math and safe-withdrawal research"),
    "Financial Mentor": ("https://financialmentor.com/calculator", "Financial planning and retirement calculators"),
}
RESEARCH = {
    "SEC EDGAR": ("https://www.sec.gov/edgar/search/", "Official US company filings and disclosures"),
    "Finviz": ("https://finviz.com/screener.ashx", "Free stock screener; use the site manually"),
    "Macrotrends": ("https://www.macrotrends.net/", "Historical company and macro charts; no automated extraction"),
    "Simply Wall St": ("https://simplywall.st/", "Visual company research; free access is limited"),
    "ETFdb": ("https://etfdb.com/", "ETF comparison and fund research"),
    "Portfolio Visualizer": ("https://www.portfoliovisualizer.com/", "Free personal-use portfolio backtests with asset/history limits"),
    "OpenInsider": ("http://openinsider.com/", "Insider transaction research"),
    "Dataroma": ("https://www.dataroma.com/", "Public 13F portfolio tracking; filings are delayed"),
    "GuruFocus": ("https://www.gurufocus.com/", "Valuation and investor research; many features are paid"),
    "Seeking Alpha": ("https://seekingalpha.com/", "Investor analysis and earnings coverage; many features are paid"),
    "MarketWatch": ("https://www.marketwatch.com/", "Market news and commentary"),
    "Morningstar": ("https://www.morningstar.com/", "Fund and equity research; many ratings/features are paid"),
    "Stock Analysis": ("https://stockanalysis.com/", "Company and ETF financials for manual review; no public API"),
    "Earnings Whispers": ("https://www.earningswhispers.com/", "Earnings calendar and expectations"),
    "JustETF": ("https://www.justetf.com/", "ETF research for European-listed funds"),
    "Trustnet": ("https://www.trustnet.com/", "UK fund research and comparisons"),
    "Xplained": ("https://xplaind.com/", "Finance and accounting calculators and explainers"),
}
MACRO = {
    "US inflation (CPI)": "https://fred.stlouisfed.org/series/CPIAUCSL",
    "Federal funds rate": "https://fred.stlouisfed.org/series/FEDFUNDS",
    "10-year Treasury": "https://fred.stlouisfed.org/series/DGS10",
    "2-year Treasury": "https://fred.stlouisfed.org/series/DGS2",
    "Unemployment": "https://fred.stlouisfed.org/series/UNRATE",
    "US dollar index (broad)": "https://fred.stlouisfed.org/series/DTWEXBGS",
    "World Bank country data": "https://data.worldbank.org/",
    "IMF data": "https://www.imf.org/en/Data",
    "BIS statistics": "https://www.bis.org/statistics/",
    "World government bond yields": "https://www.worldgovernmentbonds.com/",
}

def _f(x):
    try:
        z = float(x)
        return z if np.isfinite(z) else np.nan
    except Exception:
        return np.nan

def _fmt(x, suffix="", digits=2):
    return "N/A" if not np.isfinite(_f(x)) else f"{float(x):,.{digits}f}{suffix}"

def _load(symbol, period="5y"):
    symbol = str(symbol or "").strip().upper()
    if not symbol:
        return None, {}, ""
    try:
        frame = history(symbol, period)
        quote = info(symbol) or {}
        if frame is None or frame.empty:
            return None, quote, symbol
        return frame, quote, symbol
    except Exception as exc:
        st.warning(f"Market-data request failed: {exc}")
        return None, {}, symbol

def _resource_group(group):
    st.markdown("**Learning references**")
    rows = {
        "Screening": [("P/E ratio", "https://www.investopedia.com/terms/p/price-earningsratio.asp"), ("PEG ratio", "https://www.investopedia.com/terms/p/pegratio.asp"), ("Debt-to-equity", "https://www.investopedia.com/terms/d/debtequityratio.asp"), ("Free cash flow", "https://www.investopedia.com/terms/f/freecashflow.asp")],
        "DCF": [("DCF", "https://www.investopedia.com/terms/d/dcf.asp"), ("WACC", "https://www.investopedia.com/terms/w/wacc.asp"), ("Terminal value", "https://www.investopedia.com/terms/t/terminalvalue.asp")],
        "Risk": [("Correlation", "https://www.investopedia.com/terms/c/correlation.asp"), ("Diversification", "https://www.investopedia.com/terms/d/diversification.asp"), ("Maximum drawdown", "https://www.investopedia.com/terms/m/maximum-drawdown-mdd.asp")],
        "Earnings": [("EPS", "https://www.investopedia.com/terms/e/eps.asp"), ("Earnings surprise", "https://www.investopedia.com/terms/e/earnings-surprise.asp"), ("Guidance", "https://www.investopedia.com/terms/g/guidance.asp")],
        "Allocation": [("Asset allocation", "https://www.investopedia.com/terms/a/assetallocation.asp"), ("Rebalancing", "https://www.investopedia.com/terms/r/rebalancing.asp")],
        "Technical": [("RSI", "https://www.investopedia.com/terms/r/rsi.asp"), ("Moving average", "https://www.investopedia.com/terms/m/movingaverage.asp"), ("MACD", "https://www.investopedia.com/terms/m/macd.asp")],
        "Dividend": [("Dividend yield", "https://www.investopedia.com/terms/d/dividendyield.asp"), ("Payout ratio", "https://www.investopedia.com/terms/d/dividendpayoutratio.asp")],
        "Moat": [("Economic moat", "https://www.investopedia.com/terms/e/economicmoat.asp"), ("ROIC", "https://www.investopedia.com/terms/r/returnoninvestmentcapital.asp"), ("Porter's Five Forces", "https://www.investopedia.com/terms/p/porter.asp")],
        "Quant": [("Backtesting", "https://www.investopedia.com/terms/b/backtesting.asp"), ("Seasonality", "https://www.investopedia.com/terms/s/seasonality.asp")],
        "Macro": [("Federal funds rate", "https://www.investopedia.com/terms/f/federalfundsrate.asp"), ("Inflation", "https://www.investopedia.com/terms/i/inflation.asp"), ("Yield curve", "https://www.investopedia.com/terms/y/yieldcurve.asp")],
    }
    st.markdown(" · ".join(f"[{name}]({url})" for name, url in rows[group]))

def render_research_suite():
    st.markdown("## Institutional Research Suite")
    st.write("Ten research disciplines using free or already-available data. Investopedia and other publishers are education/reference links—not scraped data feeds.")
    ticker = st.text_input("Company ticker", value="NVDA", key="institutional_ticker").strip().upper()
    frame, q, sym = _load(ticker)
    tabs = st.tabs(["Stock Screener", "DCF Valuation", "Portfolio Risk", "Earnings", "Portfolio Builder", "Technical", "Dividends", "Competitive Advantage", "Quant Patterns", "Macro Strategy", "Research Library"])

    with tabs[0]:
        st.markdown("### Business quality and price discipline")
        if frame is not None:
            price = _f(frame["Close"].dropna().iloc[-1])
            cols = st.columns(4)
            metrics = [("Price", price, "${:,.2f}"), ("Market cap", q.get("marketCap"), "${:,.0f}"), ("Forward P/E", q.get("forwardPE"), "{:.1f}x"), ("PEG", q.get("pegRatio"), "{:.2f}x"), ("Revenue growth", q.get("revenueGrowth"), "{:.1%}"), ("Operating margin", q.get("operatingMargins"), "{:.1%}"), ("Debt/equity", q.get("debtToEquity"), "{:.1f}%"), ("Dividend yield", q.get("dividendYield"), "{:.2%}")]
            for n,(label,value,fmt) in enumerate(metrics):
                x = _f(value); cols[n%4].metric(label, fmt.format(x) if np.isfinite(x) else "N/A")
            st.caption("These are provider-reported fields, not a full five-year audited financial-statement comparison. Sector peer comparisons and cash-flow quality still need verification.")
        else:
            st.info("Enter a ticker with available market history.")
        st.markdown("[Open Finviz screener](https://finviz.com/screener.ashx) · [Open SEC EDGAR](https://www.sec.gov/edgar/search/) · [Open Stock Analysis](https://stockanalysis.com/)")
        _resource_group("Screening")

    with tabs[1]:
        st.markdown("### Editable discounted cash-flow model")
        st.caption("Uses your assumptions; it does not pretend missing free cash flow is known.")
        if frame is not None:
            default_fcf = _f(q.get("freeCashflow"))
            c1,c2,c3 = st.columns(3)
            fcf = c1.number_input("Starting annual free cash flow ($M)", min_value=0.0, value=float(max(0, default_fcf/1e6)) if np.isfinite(default_fcf) else 1000.0, step=100.0)
            growth = c2.number_input("5-year annual FCF growth (%)", min_value=-50.0, max_value=100.0, value=15.0, step=1.0)/100
            wacc = c3.number_input("Discount rate / WACC (%)", min_value=1.0, max_value=30.0, value=9.0, step=.25)/100
            c4,c5,c6 = st.columns(3)
            terminal_growth = c4.number_input("Terminal growth (%)", min_value=0.0, max_value=8.0, value=2.5, step=.25)/100
            net_debt = c5.number_input("Net debt ($M; negative = net cash)", value=0.0, step=100.0)
            shares = c6.number_input("Diluted shares (millions)", min_value=0.001, value=float(max(0.001,_f(q.get("sharesOutstanding"))/1e6)) if np.isfinite(_f(q.get("sharesOutstanding"))) else 1000.0, step=10.0)
            if wacc <= terminal_growth:
                st.error("WACC must be greater than terminal growth.")
            else:
                pv = sum((fcf*1e6*(1+growth)**year)/(1+wacc)**year for year in range(1,6))
                terminal = (fcf*1e6*(1+growth)**5*(1+terminal_growth))/(wacc-terminal_growth)
                ev = pv + terminal/(1+wacc)**5
                equity = ev - net_debt*1e6
                value_per_share = equity/(shares*1e6)
                st.metric("DCF value per share", f"${value_per_share:,.2f}")
                current = _f(frame["Close"].dropna().iloc[-1])
                st.metric("Implied upside / downside", f"{(value_per_share/current-1)*100:+.1f}%" if current>0 else "N/A")
                st.caption("Simplified enterprise DCF: five explicit years plus Gordon-growth terminal value. Validate normalized FCF, SBC/dilution, leases, pension items, cyclicality and WACC independently.")
        else: st.info("Load a company first.")
        _resource_group("DCF")

    with tabs[2]:
        st.markdown("### Portfolio risk and historical behavior")
        tickers = st.text_input("Portfolio tickers, comma-separated", "NVDA,MU,AMZN,AMD,CIBR,SHLD").upper()
        period = st.selectbox("History window", ["1y","2y","5y","10y"], index=2)
        if st.button("Calculate portfolio risk", key="risk_run"):
            symbols = list(dict.fromkeys(x.strip() for x in tickers.split(",") if x.strip()))[:20]
            series = {}
            with st.spinner("Loading adjusted price histories..."):
                for s in symbols:
                    x,_,_ = _load(s, period)
                    if x is not None and "Close" in x:
                        series[s] = x["Close"].pct_change()
            returns = pd.DataFrame(series).dropna(how="all")
            if returns.shape[1] < 2: st.warning("Need at least two tickers with overlapping price history.")
            else:
                corr = returns.corr()
                st.dataframe(corr.style.format("{:.2f}"), use_container_width=True)
                st.caption("Correlation uses daily close-to-close returns. It is historical, not a forecast of future diversification.")
                st.metric("Highest pairwise correlation", f"{corr.where(~np.eye(len(corr),dtype=bool)).max().max():.2f}")
                st.line_chart((1+returns.fillna(0)).cumprod(), use_container_width=True)
        _resource_group("Risk")

    with tabs[3]:
        st.markdown("### Earnings and catalyst review")
        if frame is not None:
            cols=st.columns(3)
            cols[0].metric("Next earnings date", str(pd.to_datetime(q.get("earningsTimestamp"),unit="s",errors="coerce").date()) if _f(q.get("earningsTimestamp"))>0 else "Not supplied")
            cols[1].metric("Forward EPS", _fmt(q.get("forwardEps"), "$"))
            cols[2].metric("Analyst count", _fmt(q.get("numberOfAnalystOpinions"), digits=0))
            st.write("Review the company's reported release, guidance and cash-flow statement before interpreting a beat or miss.")
        st.markdown("[Company filings and releases — SEC EDGAR](https://www.sec.gov/edgar/search/) · [Earnings Whispers calendar](https://www.earningswhispers.com/) · [MarketWatch](https://www.marketwatch.com/)")
        _resource_group("Earnings")

    with tabs[4]:
        st.markdown("### Allocation and rebalancing calculator")
        holdings = st.text_area("Holdings and target weights (one per line: TICKER,WEIGHT%)", "NVDA,20\nMU,15\nAMZN,15\nAMD,10\nCIBR,10\nSHLD,10\nSOFI,5\nUBER,5\nCELH,5\nCASH,5")
        rows=[]
        for line in holdings.splitlines():
            parts=line.split(",")
            if len(parts)==2:
                try: rows.append((parts[0].strip().upper(),float(parts[1].strip().replace("%",""))))
                except ValueError: pass
        total=sum(x[1] for x in rows)
        if rows:
            st.metric("Total target allocation", f"{total:.1f}%")
            if abs(total-100)>0.1: st.warning("Target weights should total 100%.")
            st.dataframe(pd.DataFrame(rows,columns=["Holding","Target weight (%)"]),use_container_width=True,hide_index=True)
            st.caption("This is a target-allocation worksheet, not personalized portfolio advice or a trade instruction.")
        _resource_group("Allocation")

    with tabs[5]:
        st.markdown("### Multi-timeframe technical intelligence")
        if frame is not None:
            close=frame["Close"].dropna()
            last=_f(close.iloc[-1])
            ma20=close.rolling(20).mean().iloc[-1]; ma50=close.rolling(50).mean().iloc[-1]; ma200=close.rolling(200).mean().iloc[-1]
            delta=close.diff(); gain=delta.clip(lower=0).rolling(14).mean(); loss=-delta.clip(upper=0).rolling(14).mean()
            rs=gain/loss.replace(0,np.nan); rsi=100-(100/(1+rs)).iloc[-1]
            c=st.columns(4)
            c[0].metric("Last price",_fmt(last,"$")); c[1].metric("20-day MA",_fmt(ma20,"$")); c[2].metric("50-day MA",_fmt(ma50,"$")); c[3].metric("RSI(14)",_fmt(rsi))
            st.line_chart(pd.DataFrame({"Close":close,"20D":close.rolling(20).mean(),"50D":close.rolling(50).mean(),"200D":close.rolling(200).mean()}),use_container_width=True)
            if np.isfinite(ma20) and np.isfinite(ma50) and np.isfinite(ma200):
                st.write("**Trend read:** " + ("Bullish alignment" if last>ma20>ma50>ma200 else "Price above key averages but not fully aligned" if last>ma50 and ma50>ma200 else "Mixed or damaged trend; wait for repair/confirmation"))
            st.caption("RSI and moving averages are descriptive indicators, not standalone buy/sell signals.")
        _resource_group("Technical")

    with tabs[6]:
        st.markdown("### Dividend quality and sustainability")
        if frame is not None:
            y=_f(q.get("dividendYield")); rate=_f(q.get("dividendRate")); payout=_f(q.get("payoutRatio"))
            c=st.columns(3); c[0].metric("Indicated dividend yield",_fmt(y*100,"%") if np.isfinite(y) else "N/A"); c[1].metric("Annual dividend/share",_fmt(rate,"$")); c[2].metric("Payout ratio",_fmt(payout*100,"%") if np.isfinite(payout) else "N/A")
            st.write("A high yield is not automatically attractive. Check free cash flow coverage, debt maturities, dividend history and whether earnings are cyclical.")
        st.markdown("[ETFdb dividend research](https://etfdb.com/) · [Morningstar](https://www.morningstar.com/)")
        _resource_group("Dividend")

    with tabs[7]:
        st.markdown("### Competitive advantage and business quality")
        if frame is not None:
            for label,key,fmt in [("Gross margin","grossMargins","{:.1%}"),("Operating margin","operatingMargins","{:.1%}"),("Return on equity","returnOnEquity","{:.1%}"),("Return on assets","returnOnAssets","{:.1%}"),("Revenue growth","revenueGrowth","{:.1%}"),("Profit growth","earningsGrowth","{:.1%}")]:
                st.write(f"**{label}:** {fmt.format(_f(q.get(key)))}" if np.isfinite(_f(q.get(key))) else f"**{label}:** Not available")
        st.markdown("**Moat checklist:** pricing power, switching costs, network effects, scale advantages, brand, patents/data, distribution and customer retention. Compare each with at least two direct peers.")
        st.markdown("[SEC filings](https://www.sec.gov/edgar/search/) · [Simply Wall St](https://simplywall.st/) · [Macrotrends](https://www.macrotrends.net/)")
        _resource_group("Moat")

    with tabs[8]:
        st.markdown("### Quant patterns and event study starter")
        if frame is not None:
            close=frame["Close"].dropna(); ret=close.pct_change().dropna()
            by_month=ret.groupby(ret.index.month).mean()*100
            month_names=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
            seasonal=pd.DataFrame({"Month":[month_names[i-1] for i in by_month.index],"Average daily return (%)":by_month.values})
            st.dataframe(seasonal,use_container_width=True,hide_index=True)
            st.caption("Exploratory monthly seasonality based on available daily observations. This is not a statistically validated trading edge; sample size, survivorship bias and multiple testing matter.")
        st.markdown("[OpenInsider — insider filings](http://openinsider.com/) · [Dataroma — 13F holdings](https://www.dataroma.com/) · [Portfolio Visualizer — backtests](https://www.portfoliovisualizer.com/)")
        _resource_group("Quant")

    with tabs[9]:
        st.markdown("### Macro regime monitor")
        st.write("Use macro data to frame rate sensitivity, inflation pressure, currency exposure and sector leadership. The links below open primary datasets; this build does not scrape third-party macro pages.")
        for label,url in MACRO.items(): st.markdown(f"- [{label}]({url})")
        st.caption("FRED API integration can be enabled later with a free FRED API key. SEC and international macro links are primary-source references.")
        _resource_group("Macro")

    with tabs[10]:
        st.markdown("### Free research and education directory")
        st.write("Free reading and manual research links. Some services mix free and paid tiers; none are treated as a guaranteed free data API.")
        st.markdown("**Education and investing philosophy**")
        for name,(url,desc) in EDUCATION.items(): st.markdown(f"- [{name}]({url}) — {desc}")
        st.markdown("**Company, ETF, market and macro research**")
        for name,(url,desc) in RESEARCH.items(): st.markdown(f"- [{name}]({url}) — {desc}")
        st.markdown("**Macro and international sources**")
        for name,url in MACRO.items(): st.markdown(f"- [{name}]({url})")
        st.info("Important: Macrotrends and StockAnalysis prohibit automated scraping/programmatic extraction under their published terms. Portfolio Visualizer's free personal tier is useful for independent backtests, but it is not an API for this app.")
