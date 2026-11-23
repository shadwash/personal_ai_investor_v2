import re
import numpy as np
import pandas as pd

def fnum(v, default=np.nan):
    try:
        x = float(v)
        return x if np.isfinite(x) else default
    except (TypeError, ValueError):
        return default

def rsi(close, period=14):
    d = close.diff()
    up = d.clip(lower=0).ewm(alpha=1/period, min_periods=period).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1/period, min_periods=period).mean()
    rs = up / dn.replace(0, np.nan)
    out = 100 - (100 / (1 + rs))
    return fnum(out.iloc[-1]) if len(out.dropna()) else np.nan

def technical_engine(h):
    if h is None or h.empty or len(h) < 60: return {}
    c = h.Close.astype(float)
    v = h.Volume.astype(float) if "Volume" in h else pd.Series(index=h.index, dtype=float)
    px = fnum(c.iloc[-1]); ma20 = c.rolling(20).mean(); ma50 = c.rolling(50).mean(); ma200 = c.rolling(200).mean()
    ret = lambda n: (px / fnum(c.iloc[-n-1]) - 1) * 100 if len(c) > n and fnum(c.iloc[-n-1]) else np.nan
    r = rsi(c); vol20 = fnum(v.tail(20).mean()); vol50 = fnum(v.tail(50).mean()); relvol = vol20 / vol50 if vol50 > 0 else np.nan
    atr = pd.concat([(h.High-h.Low), (h.High-c.shift()).abs(), (h.Low-c.shift()).abs()], axis=1).max(axis=1).rolling(14).mean().iloc[-1] if all(x in h for x in ["High", "Low"]) else np.nan
    m20=fnum(ma20.iloc[-1]); m50=fnum(ma50.iloc[-1]); m200=fnum(ma200.iloc[-1]); high20=fnum(h.High.tail(20).max()); low20=fnum(h.Low.tail(20).min())
    trend = (30 if px>m20 else 0) + (25 if px>m50 else 0) + (20 if px>m200 else 0) + (15 if m20>m50 else 0) + (10 if m50>m200 else 0)
    momentum = (30 if ret(21)>0 else 0) + (30 if ret(63)>0 else 0) + (20 if ret(126)>0 else 0) + (20 if ret(5)>0 else 0)
    rsi_score = 65 if 48<=r<=68 else 80 if 40<=r<48 else 45 if 68<r<=75 else 20 if r>75 or r<30 else 55
    volume_score = 70 if relvol>=1.2 else 55 if relvol>=0.8 else 35 if np.isfinite(relvol) else 45
    structure = 75 if px>=high20*.97 else 65 if px>m20 and px>m50 else 45 if px>=low20*1.05 else 25
    score = round(.32*trend + .28*momentum + .16*rsi_score + .12*volume_score + .12*structure, 1)
    return {"price":px,"ma20":m20,"ma50":m50,"ma200":m200,"rsi":r,"relative_volume":relvol,"atr":fnum(atr),"return_1w":ret(5),"return_1m":ret(21),"return_3m":ret(63),"return_6m":ret(126),"high20":high20,"low20":low20,"technical_score":score,"trend_score":trend,"momentum_score":momentum,"trend":"Bullish" if px>m50 and m50>m200 else "Improving" if px>m20 else "Weakening"}

def _norm(label):
    return re.sub(r"[^a-z0-9]", "", str(label).lower())

def _statement_row(frame, aliases):
    if not isinstance(frame, pd.DataFrame) or frame.empty: return []
    wanted = {_norm(x) for x in aliases}
    found = None
    for label in frame.index:
        key = _norm(label)
        if key in wanted:
            found = label; break
    if found is None:
        for label in frame.index:
            key = _norm(label)
            if any(key == w or key.startswith(w) for w in wanted):
                found = label; break
    if found is None: return []
    row = frame.loc[found]
    if isinstance(row, pd.DataFrame): row = row.iloc[0]
    vals = []
    for col, value in row.items():
        number = fnum(value)
        if np.isfinite(number): vals.append((col, number))
    try: vals.sort(key=lambda item: pd.Timestamp(item[0]), reverse=True)
    except Exception: pass
    return [v for _, v in vals]

def _first_statement_value(frame, aliases):
    values = _statement_row(frame, aliases)
    return values[0] if values else np.nan

def fundamental_engine(info, statements=None):
    """Build fundamentals from Yahoo quote fields plus reported statements. Missing is never scored as zero."""
    i = info if isinstance(info, dict) else {}
    s = statements if isinstance(statements, dict) else {}
    income=s.get("income", pd.DataFrame()); balance=s.get("balance", pd.DataFrame()); cash=s.get("cashflow", pd.DataFrame())
    metrics = {
        "revenue_growth": fnum(i.get("revenueGrowth")),
        "earnings_growth": fnum(i.get("earningsGrowth")),
        "operating_margin": fnum(i.get("operatingMargins")),
        "profit_margin": fnum(i.get("profitMargins")),
        "roe": fnum(i.get("returnOnEquity")),
        "fcf": fnum(i.get("freeCashflow")),
        "operating_cash_flow": np.nan,
        "debt_equity": fnum(i.get("debtToEquity")),
        "forward_pe": fnum(i.get("forwardPE")),
        "peg": fnum(i.get("pegRatio")),
        "market_cap": fnum(i.get("marketCap")),
    }
    sources = {k: ("Yahoo quote profile" if np.isfinite(v) else "") for k,v in metrics.items()}
    revenue = _statement_row(income, ["Total Revenue", "Operating Revenue", "Revenue"])
    net_income = _statement_row(income, ["Net Income", "Net Income Common Stockholders", "Net Income Continuous Operations"])
    operating_income = _statement_row(income, ["Operating Income", "Operating Income Loss"])
    if len(revenue) >= 2 and revenue[1] != 0:
        metrics["revenue_growth"] = revenue[0] / revenue[1] - 1; sources["revenue_growth"] = "Annual/quarterly income statement"
    if len(net_income) >= 2 and net_income[1] != 0 and net_income[1] > 0:
        metrics["earnings_growth"] = net_income[0] / net_income[1] - 1; sources["earnings_growth"] = "Annual/quarterly income statement"
    if revenue and revenue[0] != 0 and operating_income:
        metrics["operating_margin"] = operating_income[0] / revenue[0]; sources["operating_margin"] = "Income statement"
    if revenue and revenue[0] != 0 and net_income:
        metrics["profit_margin"] = net_income[0] / revenue[0]; sources["profit_margin"] = "Income statement"
    equity = _first_statement_value(balance, ["Stockholders Equity", "Total Stockholder Equity", "Common Stock Equity"])
    total_debt = _first_statement_value(balance, ["Total Debt", "Long Term Debt And Capital Lease Obligation", "Long Term Debt"])
    if np.isfinite(equity) and equity > 0 and net_income:
        metrics["roe"] = net_income[0] / equity; sources["roe"] = "Income statement / balance sheet"
    ocf = _first_statement_value(cash, ["Operating Cash Flow", "Cash Flow From Continuing Operating Activities", "Total Cash From Operating Activities"])
    capex = _first_statement_value(cash, ["Capital Expenditure", "Capital Expenditures"])
    if np.isfinite(ocf) and np.isfinite(capex):
        metrics["fcf"] = ocf - abs(capex); sources["fcf"] = "Cash flow statement"
    elif np.isfinite(ocf):
        metrics["operating_cash_flow"] = ocf; sources["operating_cash_flow"] = "Cash flow statement"
        metrics["fcf"] = np.nan; sources["fcf"] = ""
    if np.isfinite(total_debt) and np.isfinite(equity) and equity > 0:
        metrics["debt_equity"] = total_debt / equity * 100; sources["debt_equity"] = "Balance sheet"
    # Exclude metrics that are structurally misleading for banks/insurers.
    sector = str(i.get("sector", "")).lower()
    is_financial = any(x in sector for x in ["financial", "bank"])
    tests = [
        ("revenue_growth", .18, lambda x: 90 if x>.25 else 75 if x>.12 else 60 if x>0 else 25),
        ("earnings_growth", .15, lambda x: 90 if x>.25 else 75 if x>.10 else 60 if x>0 else 20),
        ("operating_margin", .14, lambda x: 90 if x>.25 else 75 if x>.15 else 60 if x>.05 else 25),
        ("profit_margin", .10, lambda x: 85 if x>.20 else 70 if x>.10 else 55 if x>0 else 20),
        ("roe", .10, lambda x: 90 if x>.20 else 75 if x>.12 else 60 if x>.05 else 25),
        ("fcf", .13, lambda x: 85 if x>0 else 20),
        ("debt_equity", .08, lambda x: 85 if x<50 else 70 if x<100 else 50 if x<180 else 20),
        ("forward_pe", .07, lambda x: 80 if 0<x<20 else 70 if x<30 else 50 if x<45 else 25),
        ("peg", .05, lambda x: 85 if 0<x<1 else 70 if x<1.5 else 50 if x<2.5 else 25),
    ]
    if is_financial:
        tests = [x for x in tests if x[0] not in ("fcf", "debt_equity")]
    total=weight=0.0; available=0
    for key,w,fn in tests:
        value=metrics[key]
        if np.isfinite(value):
            total += w*fn(value); weight += w; available += 1
    coverage = available / len(tests) * 100 if tests else 0
    # A small handful of isolated metrics is not enough to call a business weak or strong.
    score = total/weight if available >= 3 and weight > 0 else np.nan
    metrics["metric_sources"] = sources
    metrics["metrics_available"] = available
    metrics["metrics_expected"] = len(tests)
    metrics["fundamental_status"] = "Evidence available" if available >= 6 else "Limited evidence" if available >= 3 else "Insufficient data"
    return metrics, round(score,1) if np.isfinite(score) else np.nan, round(coverage,1)

def valuation_engine(info, price, statements=None):
    """
    Scenario valuation with an explicit fallback:
    1) forward EPS, then trailing EPS, using a sector reference P/E;
    2) if earnings are unavailable/negative, revenue per share using a
       conservative sector reference P/S range.
    Multiples are transparent assumptions, not analyst consensus targets.
    """
    i = info if isinstance(info, dict) else {}
    s = statements if isinstance(statements, dict) else {}
    sector = str(i.get("sector", "")).lower()
    eps_forward = fnum(i.get("forwardEps"))
    eps_trailing = fnum(i.get("trailingEps"))
    inputs = {
        "current_price": fnum(price),
        "forward_eps": eps_forward,
        "trailing_eps": eps_trailing,
        "forward_pe_reported": fnum(i.get("forwardPE")),
        "price_to_sales_reported": fnum(i.get("priceToSalesTrailing12Months")),
        "sector": i.get("sector", "Not provided"),
        "industry": i.get("industry", "Not provided"),
    }

    pe_targets = [
        (("technology", "communication services"), 25.0),
        (("healthcare",), 22.0),
        (("financial",), 14.0),
        (("consumer defensive",), 20.0),
        (("consumer cyclical",), 19.0),
        (("industrials",), 20.0),
        (("energy",), 14.0),
        (("utilities",), 17.0),
        (("real estate",), 18.0),
        (("basic materials",), 16.0),
    ]
    ps_targets = [
        (("technology", "communication services"), 4.0),
        (("healthcare",), 3.5),
        (("financial",), 2.0),
        (("consumer defensive",), 1.5),
        (("consumer cyclical",), 1.8),
        (("industrials",), 2.0),
        (("energy",), 1.5),
        (("utilities",), 2.0),
        (("real estate",), 3.0),
        (("basic materials",), 2.0),
    ]
    def sector_multiple(table, default):
        for terms, multiple in table:
            if any(term in sector for term in terms):
                return multiple
        return default

    if not np.isfinite(price) or price <= 0:
        return {"fair_value":np.nan,"bear":np.nan,"base":np.nan,"bull":np.nan,
                "valuation_note":"Unavailable: a valid current share price was not returned.",
                "valuation_method":"Unavailable","valuation_inputs":inputs}

    eps = eps_forward if np.isfinite(eps_forward) and eps_forward > 0 else eps_trailing
    if np.isfinite(eps) and eps > 0:
        target_pe = sector_multiple(pe_targets, 20.0)
        bear = eps * target_pe * 0.75
        base = eps * target_pe
        bull = eps * target_pe * 1.25
        method = "Earnings-based"
        source = "forward EPS" if np.isfinite(eps_forward) and eps_forward > 0 else "trailing EPS"
        note = (f"{source} of ${eps:.2f} × sector reference P/E of {target_pe:.1f}×. "
                "Bear/base/bull use 75%/100%/125% of that reference multiple. "
                "This is a transparent screening estimate, not a price target from an analyst.")
        inputs.update({"eps_used":eps,"eps_source":source,"reference_pe":target_pe})
    else:
        income = s.get("income", pd.DataFrame())
        revenue_values = _statement_row(income, ["Total Revenue", "Operating Revenue", "Revenue"])
        revenue = fnum(i.get("totalRevenue"))
        if not np.isfinite(revenue) and revenue_values:
            revenue = revenue_values[0]
        shares = fnum(i.get("sharesOutstanding"))
        if (not np.isfinite(shares) or shares <= 0) and np.isfinite(fnum(i.get("marketCap"))):
            shares = fnum(i.get("marketCap")) / price
        revenue_per_share = revenue / shares if np.isfinite(revenue) and revenue > 0 and np.isfinite(shares) and shares > 0 else np.nan
        inputs.update({"revenue":revenue,"shares_outstanding":shares,"revenue_per_share":revenue_per_share})
        if np.isfinite(revenue_per_share) and revenue_per_share > 0:
            target_ps = sector_multiple(ps_targets, 2.0)
            bear = revenue_per_share * target_ps * 0.65
            base = revenue_per_share * target_ps
            bull = revenue_per_share * target_ps * 1.40
            method = "Sales-based (earnings unavailable)"
            note = (f"Revenue per share of ${revenue_per_share:.2f} × sector reference P/S of {target_ps:.1f}×. "
                    "Bear/base/bull use 65%/100%/140% of that reference multiple. "
                    "Sales-based valuation is less reliable because it does not fully account for margins, debt or dilution.")
            inputs.update({"reference_ps":target_ps,"revenue_source":"Yahoo profile or reported income statement"})
        else:
            return {"fair_value":np.nan,"bear":np.nan,"base":np.nan,"bull":np.nan,
                    "valuation_note":"Unavailable: neither positive EPS nor usable revenue-per-share data was returned. Review the company’s reported statements; do not invent a valuation.",
                    "valuation_method":"Insufficient data","valuation_inputs":inputs}

    upside = (base / price - 1) * 100
    return {"fair_value":base,"bear":bear,"base":base,"bull":bull,
            "fair_value_upside":upside,"valuation_note":note,
            "valuation_method":method,"valuation_inputs":inputs}

def entry_engine(t):
    p=t.get("price",np.nan); a=t.get("atr",np.nan); m20=t.get("ma20",np.nan); m50=t.get("ma50",np.nan); low=t.get("low20",np.nan); high=t.get("high20",np.nan)
    if not np.isfinite(p) or p<=0: return {}
    atr=a if np.isfinite(a) and a>0 else p*.03
    support=max(x for x in [m20,m50,low] if np.isfinite(x) and x<p) if any(np.isfinite(x) and x<p for x in [m20,m50,low]) else p-atr
    early_low=max(0,support-atr*.35); early_high=support+atr*.15
    pullback_low=max(0,support-atr*.15); pullback_high=support+atr*.35
    breakout=high*1.005 if np.isfinite(high) else p+atr
    stop=max(0,support-atr*1.25)
    return {"early_low":early_low,"early_high":early_high,"pullback_low":pullback_low,"pullback_high":pullback_high,"breakout":breakout,"invalidation":stop,"technical_target_1":p+atr*2,"technical_target_2":p+atr*3.5}

def shield_engine(fund, tech, valuation, entry, info):
    flags=[]; risks=[]
    if not np.isfinite(fund): flags.append("Insufficient fundamental data — provider fields/statements did not supply at least three usable metrics")
    elif fund<45: flags.append("Weak fundamental profile — supported by available financial metrics")
    if not np.isfinite(tech): flags.append("Insufficient technical history")
    elif tech<40: flags.append("Weak technical structure")
    upside=valuation.get("fair_value_upside",np.nan)
    if np.isfinite(upside) and upside < -15: flags.append("Price materially above simplified fair-value estimate")
    if info.get("quoteType") not in (None,"EQUITY"): flags.append("Instrument may not be a common equity")
    if info.get("earningsTimestamp"): risks.append("Check upcoming earnings date before acting")
    if not entry: flags.append("Entry levels unavailable")
    return {"flags":flags,"notes":risks,"status":"Needs caution" if flags else "No major screen-level flags","coverage_warning":not np.isfinite(fund)}

def opportunity_score(fund, tech, valuation_upside, catalyst_score=50):
    parts=[]
    if np.isfinite(fund): parts.append((fund,.35))
    if np.isfinite(tech): parts.append((tech,.35))
    if np.isfinite(valuation_upside):
        val=85 if valuation_upside>30 else 75 if valuation_upside>15 else 60 if valuation_upside>0 else 35 if valuation_upside>-15 else 15
        parts.append((val,.20))
    parts.append((catalyst_score,.10))
    return round(sum(v*w for v,w in parts)/sum(w for _,w in parts),1) if parts else np.nan
