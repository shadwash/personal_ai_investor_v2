import numpy as np
import pandas as pd


def fnum(v, default=np.nan):
    try:
        x=float(v)
        return x if np.isfinite(x) else default
    except (TypeError, ValueError): return default

def rsi(close, period=14):
    d=close.diff(); up=d.clip(lower=0).ewm(alpha=1/period,min_periods=period).mean(); dn=(-d.clip(upper=0)).ewm(alpha=1/period,min_periods=period).mean()
    rs=up/dn.replace(0,np.nan); out=100-(100/(1+rs))
    return fnum(out.iloc[-1]) if len(out.dropna()) else np.nan

def technical_engine(h):
    if h is None or h.empty or len(h)<60: return {}
    c=h.Close.astype(float); v=h.Volume.astype(float) if "Volume" in h else pd.Series(index=h.index,dtype=float)
    px=fnum(c.iloc[-1]); ma20=c.rolling(20).mean(); ma50=c.rolling(50).mean(); ma200=c.rolling(200).mean()
    ret=lambda n: (px/fnum(c.iloc[-n-1])-1)*100 if len(c)>n and fnum(c.iloc[-n-1]) else np.nan
    r=rsi(c); vol20=fnum(v.tail(20).mean()); vol50=fnum(v.tail(50).mean()); relvol=vol20/vol50 if vol50>0 else np.nan
    atr=pd.concat([(h.High-h.Low),(h.High-c.shift()).abs(),(h.Low-c.shift()).abs()],axis=1).max(axis=1).rolling(14).mean().iloc[-1] if all(x in h for x in ["High","Low"]) else np.nan
    m20=fnum(ma20.iloc[-1]); m50=fnum(ma50.iloc[-1]); m200=fnum(ma200.iloc[-1]); high20=fnum(h.High.tail(20).max()); low20=fnum(h.Low.tail(20).min())
    trend=0
    trend += 30 if px>m20 else 0; trend += 25 if px>m50 else 0; trend += 20 if px>m200 else 0
    trend += 15 if m20>m50 else 0; trend += 10 if m50>m200 else 0
    momentum=0
    momentum += 30 if ret(21)>0 else 0; momentum += 30 if ret(63)>0 else 0; momentum += 20 if ret(126)>0 else 0; momentum += 20 if ret(5)>0 else 0
    rsi_score=65 if 48<=r<=68 else 80 if 40<=r<48 else 45 if 68<r<=75 else 20 if r>75 or r<30 else 55
    volume_score=70 if relvol>=1.2 else 55 if relvol>=0.8 else 35 if np.isfinite(relvol) else 45
    structure=75 if px>=high20*.97 else 65 if px>m20 and px>m50 else 45 if px>=low20*1.05 else 25
    score=round(.32*trend+.28*momentum+.16*rsi_score+.12*volume_score+.12*structure,1)
    return {"price":px,"ma20":m20,"ma50":m50,"ma200":m200,"rsi":r,"relative_volume":relvol,"atr":fnum(atr),"return_1w":ret(5),"return_1m":ret(21),"return_3m":ret(63),"return_6m":ret(126),"high20":high20,"low20":low20,"technical_score":score,"trend_score":trend,"momentum_score":momentum,"trend":"Bullish" if px>m50 and m50>m200 else "Improving" if px>m20 else "Weakening"}

def fundamental_engine(i):
    metrics={"revenue_growth":fnum(i.get("revenueGrowth")),"earnings_growth":fnum(i.get("earningsGrowth")),"operating_margin":fnum(i.get("operatingMargins")),"profit_margin":fnum(i.get("profitMargins")),"roe":fnum(i.get("returnOnEquity")),"fcf":fnum(i.get("freeCashflow")),"debt_equity":fnum(i.get("debtToEquity")),"forward_pe":fnum(i.get("forwardPE")),"peg":fnum(i.get("pegRatio")),"market_cap":fnum(i.get("marketCap"))}
    # Missing fields are omitted from weighted score; coverage is reported separately.
    tests=[("revenue_growth",.18,lambda x: 90 if x>.25 else 75 if x>.12 else 60 if x>0 else 25),("earnings_growth",.15,lambda x: 90 if x>.25 else 75 if x>.10 else 60 if x>0 else 20),("operating_margin",.14,lambda x: 90 if x>.25 else 75 if x>.15 else 60 if x>.05 else 25),("profit_margin",.10,lambda x: 85 if x>.20 else 70 if x>.10 else 55 if x>0 else 20),("roe",.10,lambda x: 90 if x>.20 else 75 if x>.12 else 60 if x>.05 else 25),("fcf",.13,lambda x: 85 if x>0 else 20),("debt_equity",.08,lambda x: 85 if x<50 else 70 if x<100 else 50 if x<180 else 20),("forward_pe",.07,lambda x: 80 if 0<x<20 else 70 if x<30 else 50 if x<45 else 25),("peg",.05,lambda x: 85 if 0<x<1 else 70 if x<1.5 else 50 if x<2.5 else 25)]
    total=weight=available=0
    for key,w,fn in tests:
        x=metrics[key]
        if np.isfinite(x): total+=w*fn(x); weight+=w; available+=1
    coverage=available/len(tests)*100
    score=total/weight if weight else np.nan
    return metrics,round(score,1) if np.isfinite(score) else np.nan,round(coverage,1)

def valuation_engine(info, price):
    eps=fnum(info.get("forwardEps")); pe=fnum(info.get("forwardPE")); sector=fnum(info.get("forwardPE"))
    if not np.isfinite(eps) or eps<=0 or not np.isfinite(price) or price<=0:
        return {"fair_value":np.nan,"bear":np.nan,"base":np.nan,"bull":np.nan,"valuation_note":"Unavailable: positive forward EPS and a usable current price are required."}
    # Transparent, deliberately simple multiple model; not a DCF or analyst consensus.
    base_multiple=min(max(pe if np.isfinite(pe) else 18,10),35)
    bear=eps*max(8,base_multiple*.72); base=eps*base_multiple; bull=eps*min(45,base_multiple*1.25)
    return {"fair_value":base,"bear":bear,"base":base,"bull":bull,"valuation_note":f"Forward EPS × current forward P/E ({base_multiple:.1f}x). Scenario multiples are illustrative sensitivity assumptions."}

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
    if not np.isfinite(fund): flags.append("Insufficient fundamental data")
    elif fund<45: flags.append("Weak fundamental profile")
    if not np.isfinite(tech): flags.append("Insufficient technical history")
    elif tech<40: flags.append("Weak technical structure")
    upside=valuation.get("fair_value_upside",np.nan)
    if np.isfinite(upside) and upside < -15: flags.append("Price materially above simplified fair-value estimate")
    if info.get("quoteType") not in (None,"EQUITY"): flags.append("Instrument may not be a common equity")
    if info.get("earningsTimestamp"):
        risks.append("Check upcoming earnings date before acting")
    if not entry: flags.append("Entry levels unavailable")
    return {"flags":flags,"notes":risks,"status":"Needs caution" if flags else "No major screen-level flags", "coverage_warning":not np.isfinite(fund)}

def opportunity_score(fund, tech, valuation_upside, catalyst_score=50):
    parts=[]
    if np.isfinite(fund): parts.append((fund,.35))
    if np.isfinite(tech): parts.append((tech,.35))
    if np.isfinite(valuation_upside):
        val=85 if valuation_upside>30 else 75 if valuation_upside>15 else 60 if valuation_upside>0 else 35 if valuation_upside>-15 else 15
        parts.append((val,.20))
    parts.append((catalyst_score,.10))
    return round(sum(v*w for v,w in parts)/sum(w for _,w in parts),1) if parts else np.nan
