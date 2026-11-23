import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import numpy as np
import pandas as pd
import streamlit as st
from config import APP_NAME, APP_TAGLINE, DEFAULT_SCAN, MAX_SCAN, SECTOR_ETFS
from data.market_data import discover_universe, history, info, sector_etf_history
from research.company_research import research_company
from charts.price_chart import build_chart
from storage.history import record_research, log_frame
from engines.agent_committee import run_committee
from research.institutional_suite import render_research_suite

st.set_page_config(page_title=APP_NAME,page_icon="📈",layout="wide",initial_sidebar_state="expanded")
st.markdown("""
<style>
:root{color-scheme:dark}
.stApp{background:radial-gradient(ellipse at 12% 0%,rgba(20,184,166,.10),transparent 34%),radial-gradient(ellipse at 88% 8%,rgba(59,130,246,.10),transparent 30%),#080f1c;color:#e6edf7}
.block-container{max-width:1540px;padding-top:1.25rem;padding-bottom:3.5rem}
[data-testid="stHeader"]{background:rgba(8,15,28,.82)}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0d192b 0%,#0a1220 100%);border-right:1px solid #1e3048}
[data-testid="stSidebar"] *{color:#d9e5f5}
[data-testid="stSidebar"] [data-testid="stRadio"] label{padding:.48rem .65rem;border-radius:9px}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover{background:#172940}
.hero{position:relative;overflow:hidden;background:linear-gradient(112deg,#10243b 0%,#102d3b 48%,#123b43 100%);border:1px solid #24546a;border-radius:20px;padding:1.7rem 1.9rem;margin-bottom:1.5rem;box-shadow:0 16px 42px rgba(0,0,0,.24)}
.hero:after{content:"";position:absolute;width:260px;height:260px;right:-65px;top:-145px;border:1px solid rgba(45,212,191,.28);border-radius:50%;box-shadow:0 0 0 24px rgba(45,212,191,.035),0 0 0 50px rgba(45,212,191,.025)}
.kicker{font-size:.68rem;letter-spacing:.19em;font-weight:850;color:#5eead4;text-transform:uppercase}
.hero h1{font-size:2.15rem;line-height:1.12;letter-spacing:.025em;margin:.42rem 0;color:#f8fbff}
.hero p{color:#b7c9dc;margin:0;font-size:.96rem;max-width:850px}
.panel{background:linear-gradient(145deg,#111f32,#0e1a2b);border:1px solid #243952;border-radius:14px;padding:1rem 1.1rem}
h1,h2,h3{color:#f1f6ff!important;letter-spacing:-.02em}
h2{padding-bottom:.45rem;border-bottom:1px solid #24374e}
h3{color:#75e4d1!important}
p,li,label,.stMarkdown{color:#d3deec}
small,[data-testid="stCaptionContainer"]{color:#8fa5bd!important}
div[data-testid="stMetric"]{background:linear-gradient(145deg,#14263b,#101d30);border:1px solid #2b4562;padding:.95rem 1rem;border-radius:13px;box-shadow:0 8px 22px rgba(0,0,0,.16);min-height:104px}
div[data-testid="stMetric"] label{color:#9db3cb!important;font-size:.76rem!important;text-transform:uppercase;letter-spacing:.07em}
div[data-testid="stMetric"] [data-testid="stMetricValue"]{color:#f4f8ff!important;font-weight:750}
div[data-testid="stMetric"] [data-testid="stMetricDelta"]{font-weight:700}
.stButton>button{border-radius:10px;font-weight:750;border:1px solid #34506d;background:#17283d;color:#e8f2ff;transition:all .18s ease}
.stButton>button:hover{border-color:#2dd4bf;color:#5eead4;background:#183448}
.stButton>button[kind="primary"]{background:linear-gradient(100deg,#087f8c,#2563eb);color:white;border:1px solid #2997b3;box-shadow:0 7px 20px rgba(8,145,178,.2)}
.stButton>button[kind="primary"]:hover{background:linear-gradient(100deg,#0d9aa6,#3478f6);border-color:#5eead4}
[data-testid="stDataFrame"],[data-testid="stTable"]{border:1px solid #263d56;border-radius:12px;overflow:hidden;background:#101d2e}
[data-testid="stExpander"]{border:1px solid #263d56;border-radius:12px;background:rgba(17,31,50,.72)}
[data-testid="stAlert"]{border-radius:12px;border:1px solid #2b4562;background:#13243a}
[data-testid="stTextInput"] input,[data-testid="stNumberInput"] input,[data-testid="stSelectbox"]>div>div{background:#101f32;color:#edf5ff;border-color:#304a66;border-radius:9px}
[data-testid="stProgressBar"]>div>div{background:linear-gradient(90deg,#14b8a6,#3b82f6)}
hr{border-color:#26394f}
a{color:#5eead4!important}
/* Consistent dark surfaces across native Streamlit widgets */
.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"],[data-testid="stMainBlockContainer"]{background-color:#080f1c;color:#e6edf7}
[data-testid="stVerticalBlock"]>div{color:inherit}
[data-testid="stTabs"] [role="tablist"]{border-bottom:1px solid #263d56;gap:.35rem}
[data-testid="stTabs"] button[role="tab"]{color:#a9bdd3;border-radius:9px 9px 0 0}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"]{color:#5eead4;border-bottom:2px solid #14b8a6}
[data-baseweb="select"]>div,[data-baseweb="input"]>div,[data-baseweb="textarea"]>div{background:#101f32!important;border-color:#304a66!important;color:#edf5ff!important}
[data-baseweb="popover"],[data-baseweb="menu"],[role="listbox"]{background:#14243a!important;border:1px solid #304a66!important;color:#edf5ff!important}
[role="option"]{background:#14243a!important;color:#edf5ff!important}
[role="option"]:hover,[aria-selected="true"]{background:#1b3850!important}
[data-testid="stDateInput"] input,[data-testid="stTimeInput"] input,[data-testid="stTextArea"] textarea{background:#101f32!important;color:#edf5ff!important;border:1px solid #304a66!important}
[data-testid="stCheckbox"] label,[data-testid="stRadio"] label,[data-testid="stSlider"] label{color:#d3deec!important}
[data-testid="stExpander"] summary,[data-testid="stExpander"] details{background:#111f32!important;color:#e6edf7!important}
[data-testid="stAlert"] p,[data-testid="stAlert"] div{color:#e6edf7}
[data-testid="stDataFrame"],[data-testid="stTable"]{background:#101d2e!important}
[data-testid="stCode"],pre,code{background:#101d2e!important;color:#dce9f7!important;border-color:#263d56!important}
[data-testid="stPlotlyChart"]{background:#0d192b;border:1px solid #263d56;border-radius:13px;padding:.35rem}
iframe{color-scheme:dark}
::selection{background:rgba(20,184,166,.35);color:#fff}
@media(max-width:700px){.hero{padding:1.25rem}.hero h1{font-size:1.65rem}.block-container{padding-left:1rem;padding-right:1rem}}
</style>
<div class="hero"><div class="kicker">Independent research desk · Version 2.0</div><h1>PERSONAL AI INVESTOR</h1><p>Discover exceptional businesses. Challenge the evidence. Find attractive prices before chasing becomes the only option.</p></div>
""",unsafe_allow_html=True)

PAGES=["Command Center","Market Opportunities","Industry & ETF Discovery","Company Research","Entry & Risk","Swing Research","AI Investment Committee","Institutional Research Suite","Research History","Methodology"]
with st.sidebar:
    st.markdown("### PERSONAL AI INVESTOR")
    page=st.radio("Research workspace",PAGES,label_visibility="collapsed")
    st.divider(); st.caption("Free-data research edition")
    st.caption("No brokerage connection. No automated trade execution.")

def money(x):
    try: return "N/A" if not np.isfinite(float(x)) else f"${float(x):,.2f}"
    except Exception:return "N/A"
def val(x,suffix=""):
    try:return "N/A" if not np.isfinite(float(x)) else f"{float(x):.1f}{suffix}"
    except Exception:return "N/A"
def company_name(d):return d["info"].get("longName") or d["info"].get("shortName") or d["symbol"]
def research_table(rows):
    if not rows: st.info("No candidates returned. Free screeners can be rate-limited or incomplete; try again later or use Company Research.");return
    df=pd.DataFrame(rows)
    preferred=["Ticker","Company","Price","1W Return","1M Return","3M Return","RSI","Trend","Chart Read","Opportunity Score","Business Score","Technical Score","Momentum Score","Fundamental Coverage","Fair Value Upside","Desk Flags"]
    df=df[[c for c in preferred if c in df.columns]]
    st.dataframe(df,use_container_width=True,hide_index=True,height=min(560,42+35*min(len(df),14)),column_config={"Price":st.column_config.NumberColumn(format="$%.2f"),"1W Return":st.column_config.NumberColumn(format="%.1f%%"),"1M Return":st.column_config.NumberColumn(format="%.1f%%"),"3M Return":st.column_config.NumberColumn(format="%.1f%%"),"RSI":st.column_config.NumberColumn(format="%.1f"),"Fair Value Upside":st.column_config.NumberColumn(format="%.1f%%"),"Business Score":st.column_config.NumberColumn(format="%.1f"),"Technical Score":st.column_config.NumberColumn(format="%.1f"),"Momentum Score":st.column_config.NumberColumn(format="%.1f"),"Opportunity Score":st.column_config.NumberColumn(format="%.1f"),"Fundamental Coverage":st.column_config.NumberColumn(format="%.0f%%")})


def fundamentals_story(m, info):
    def pct(key):
        x=m.get(key,np.nan)
        return f"{x*100:.1f}%" if np.isfinite(x) else "not available"
    def cash(key):
        x=m.get(key,np.nan)
        if not np.isfinite(x): return "not available"
        return "$"+(f"{x/1e9:.2f}B" if abs(x)>=1e9 else f"{x/1e6:.1f}M")
    rev=m.get("revenue_growth",np.nan); earn=m.get("earnings_growth",np.nan)
    op=m.get("operating_margin",np.nan); margin=m.get("profit_margin",np.nan)
    roe=m.get("roe",np.nan); fcf=m.get("fcf",np.nan); debt=m.get("debt_equity",np.nan)
    pe=m.get("forward_pe",np.nan); peg=m.get("peg",np.nan)
    parts=[]
    if np.isfinite(rev):
        parts.append(("Growth",f"Revenue growth is {pct('revenue_growth')}. " + ("That is a strong growth rate." if rev>=.20 else "That is moderate growth; check whether it is accelerating." if rev>=.05 else "Growth is weak or negative, so the company needs a clear explanation for the slowdown.")))
    else: parts.append(("Growth","Revenue growth was not returned, so the growth story cannot be confirmed from this data pull."))
    if np.isfinite(earn):
        parts.append(("Earnings",f"Earnings growth is {pct('earnings_growth')}. " + ("Profits are growing at a strong pace." if earn>=.15 else "Profit growth is modest or under pressure; compare it with revenue growth." if earn>=0 else "Earnings are declining; determine whether this is temporary investment or deteriorating economics.")))
    else: parts.append(("Earnings","Earnings growth is unavailable; don't assume revenue growth is translating into profits."))
    if np.isfinite(op) or np.isfinite(margin):
        sentence="Operating margin is "+pct("operating_margin") if np.isfinite(op) else "Operating margin is unavailable"
        sentence += "; net profit margin is "+pct("profit_margin") if np.isfinite(margin) else "; net profit margin is unavailable"
        if np.isfinite(op): sentence += ". " + ("The operating margin suggests meaningful pricing power or operating leverage." if op>=.20 else "The operating margin is positive but needs comparison with peers and its own history." if op>0 else "Negative operating margin means the core operation is not currently profitable.")
        parts.append(("Profitability",sentence))
    else: parts.append(("Profitability","Margin data is missing, so profitability quality cannot be established."))
    if np.isfinite(roe):
        parts.append(("Returns",f"Return on equity is {pct('roe')}. " + ("This is a strong reported return on shareholder equity." if roe>=.15 else "This is a moderate or weak return; compare with peers and leverage.")))
    if np.isfinite(fcf):
        parts.append(("Cash generation",f"Reported free cash flow field is {cash('fcf')}. " + ("Positive cash generation gives the business more flexibility." if fcf>0 else "Negative cash flow means the company is consuming cash; determine whether this is investment or stress.")))
    elif np.isfinite(m.get("operating_cash_flow",np.nan)):
        parts.append(("Cash generation","Operating cash flow is "+cash("operating_cash_flow")+", but capital expenditure was unavailable, so free cash flow cannot be calculated reliably from this data pull."))
    else: parts.append(("Cash generation","Free cash flow is unavailable. We should not infer cash generation from earnings alone."))
    if np.isfinite(debt):
        parts.append(("Balance sheet",f"Debt-to-equity is {debt:.1f}%. " + ("Leverage appears relatively contained on this measure." if debt<50 else "Leverage deserves attention; compare debt maturities, interest expense and cash flow." if debt<150 else "Leverage is high on this measure and could increase financial risk.")))
    else: parts.append(("Balance sheet","Debt-to-equity was not returned; review the balance sheet and debt maturities before drawing a conclusion."))
    if np.isfinite(pe):
        parts.append(("Valuation",f"Forward P/E is {pe:.1f}×. " + ("The multiple is relatively modest, but only attractive if earnings estimates are credible." if pe<20 else "The market is paying a growth premium; the business must deliver to justify it." if pe<35 else "The market is pricing in substantial future success, leaving less room for disappointment.")))
    else: parts.append(("Valuation","Forward P/E is unavailable, so the current earnings multiple cannot be assessed."))
    if np.isfinite(peg): parts.append(("Growth-adjusted valuation",f"PEG is {peg:.2f}×. Treat this as a rough cross-check, not a standalone valuation decision."))
    return parts

def investment_readout(t, m, v, e):
    tech=t.get("technical_score",np.nan); status=m.get("fundamental_status","Insufficient data")
    rev=m.get("revenue_growth",np.nan); earn=m.get("earnings_growth",np.nan); fcf=m.get("fcf",np.nan)
    price=t.get("price",np.nan); upside=v.get("fair_value_upside",np.nan)
    if np.isfinite(tech) and tech>=70 and np.isfinite(price) and np.isfinite(t.get("ma50",np.nan)) and price>t["ma50"]:
        chart_verdict="The chart is constructive. Price strength is supported by technical evidence, but check whether it is near support or already extended before entering."
    elif np.isfinite(tech) and tech<45:
        chart_verdict="The chart is weak. The business may still deserve research, but price action does not yet support an aggressive entry."
    else:
        chart_verdict="The chart is mixed or developing. Wait for confirmation that price can hold support and reclaim resistance."
    if status=="Insufficient data":
        business_verdict="The business cannot be rated confidently from the available free-data fields. Missing information is not proof of a bad company."
    elif np.isfinite(rev) and rev>0 and np.isfinite(earn) and earn>0 and np.isfinite(fcf) and fcf>0:
        business_verdict="The available figures show revenue and earnings growth alongside positive free cash flow. That is promising; verify durability, margins, debt and peer valuation."
    elif np.isfinite(rev) and rev>0 and (not np.isfinite(earn) or earn<=0):
        business_verdict="Sales are growing, but earnings are not confirming the growth yet. The key question is whether margins can expand or costs are structurally high."
    elif np.isfinite(fcf) and fcf<0:
        business_verdict="Cash generation is a concern. Determine whether negative free cash flow reflects deliberate growth investment or a business model that consumes too much cash."
    else:
        business_verdict="The fundamentals are mixed. The individual growth, profitability and balance-sheet facts below matter more than a composite grade."
    valuation_verdict=f" The simplified fair-value model indicates {upside:+.1f}% upside/downside." if np.isfinite(upside) else " The simplified valuation model is unavailable, so price attractiveness still needs independent work."
    return chart_verdict, business_verdict+valuation_verdict

def technical_story(t):
    px=t.get("price",np.nan); m20=t.get("ma20",np.nan); m50=t.get("ma50",np.nan); m200=t.get("ma200",np.nan)
    rsi=t.get("rsi",np.nan); rv=t.get("relative_volume",np.nan)
    r1=t.get("return_1w",np.nan); r1m=t.get("return_1m",np.nan); r3=t.get("return_3m",np.nan)
    high=t.get("high20",np.nan); low=t.get("low20",np.nan)
    above20=np.isfinite(px) and np.isfinite(m20) and px>m20
    above50=np.isfinite(px) and np.isfinite(m50) and px>m50
    above200=np.isfinite(px) and np.isfinite(m200) and px>m200
    aligned=np.isfinite(m20) and np.isfinite(m50) and np.isfinite(m200) and m20>m50>m200
    if aligned and above20:
        trend_text="The primary trend is constructive: price is above its 20-, 50- and 200-day averages, and the averages are stacked bullishly."
    elif above50 and above200:
        trend_text="The intermediate and long-term trend remain constructive, but the short-term picture needs confirmation."
    elif above20 and not above50:
        trend_text="Price is trying to improve above its 20-day average, but it has not reclaimed the 50-day trend line. This is an early repair attempt, not a confirmed uptrend."
    elif not above200:
        trend_text="Price remains below its 200-day average. The larger trend is damaged; any bounce should be treated cautiously until important averages are reclaimed."
    else:
        trend_text="The moving-average picture is mixed. Wait for price and the key averages to align before treating the move as a durable trend."
    momentum_text = ("Momentum is accelerating across the measured periods." if np.isfinite(r1m) and np.isfinite(r3) and r1m>0 and r3>0 else "Short-term momentum is positive, but the larger three-month move is still negative." if np.isfinite(r1m) and np.isfinite(r3) and r1m>0>=r3 else "Momentum is fading or negative; look for a higher low and a reclaim of short-term resistance before assuming a reversal." if np.isfinite(r1m) and r1m<=0 else "Momentum readings are mixed or incomplete.")
    if np.isfinite(rsi):
        rsi_text=f"RSI is {rsi:.1f} — " + ("overbought; avoid treating strength alone as a fresh entry signal." if rsi>=70 else "oversold; watch for stabilization rather than buying weakness blindly." if rsi<=30 else "in a constructive middle range." if 50<=rsi<70 else "below the 50 line, so momentum has not fully turned positive.")
    else:rsi_text="RSI is unavailable from the current price history."
    volume_text=f"Recent volume is {rv:.2f}× its 50-day average." if np.isfinite(rv) else "Relative volume is unavailable."
    if np.isfinite(rv) and rv>=1.5: volume_text += " Participation is notably elevated; check whether volume confirms an advance or signals distribution."
    elif np.isfinite(rv) and rv<0.7: volume_text += " Participation is light, so breakouts may lack conviction."
    proximity = (high/px-1)*100 if np.isfinite(high) and np.isfinite(px) and px>0 else np.nan
    structure_text=f"Price is {proximity:.1f}% below its 20-day high." if np.isfinite(proximity) else "Recent price structure is incomplete."
    return {"trend":trend_text,"momentum":momentum_text,"rsi":rsi_text,"volume":volume_text,"structure":structure_text}


def financial_history_frame(data):
    """Build a compact reported financial history table from available Yahoo statements."""
    statements=data.get("financial_statements",{}) or {}
    aliases={
        "Revenue":["Total Revenue","Operating Revenue","Revenue"],
        "Operating income":["Operating Income"],
        "Net income":["Net Income","Net Income Common Stockholders"],
        "Operating cash flow":["Operating Cash Flow","Cash Flow From Continuing Operating Activities"],
        "Capital expenditures":["Capital Expenditure","Capital Expenditures"],
        "Free cash flow":["Free Cash Flow"],
        "Total debt":["Total Debt","Long Term Debt And Capital Lease Obligation"],
        "Cash and equivalents":["Cash And Cash Equivalents","Cash Cash Equivalents And Short Term Investments"],
    }
    rows=[]
    for label,keys in aliases.items():
        frame_key="cashflow" if label in ("Operating cash flow","Capital expenditures","Free cash flow") else "balance" if label in ("Total debt","Cash and equivalents") else "income"
        frame=statements.get(frame_key)
        if not isinstance(frame,pd.DataFrame) or frame.empty: continue
        wanted={str(k).lower().replace(" ","").replace("_","") for k in keys}
        found=None
        for idx in frame.index:
            normalized=str(idx).lower().replace(" ","").replace("_","")
            if normalized in wanted or any(normalized.startswith(k) for k in wanted):
                found=idx; break
        if found is None: continue
        series=frame.loc[found]
        if isinstance(series,pd.DataFrame): series=series.iloc[0]
        row={"Metric":label}
        for col,value in series.items():
            try:
                number=float(value)
                if np.isfinite(number):
                    try: period=pd.Timestamp(col).strftime("%Y")
                    except Exception: period=str(col)
                    row[period]=number/1e9
            except Exception: pass
        if len(row)>1: rows.append(row)
    if not rows: return pd.DataFrame()
    result=pd.DataFrame(rows).set_index("Metric")
    result=result.loc[:,~result.columns.duplicated()]
    return result.round(2)


def sector_relative_context(data):
    """Compare the stock with its broad sector ETF using the same cached price source."""
    sector=str(data.get("info",{}).get("sector","")).strip()
    mapping={
        "Technology":"Technology","Financial Services":"Financials","Healthcare":"Healthcare",
        "Consumer Defensive":"Consumer Staples","Consumer Cyclical":"Consumer Discretionary",
        "Industrials":"Industrials","Energy":"Energy","Utilities":"Utilities",
        "Basic Materials":"Materials","Real Estate":"Real Estate",
        "Communication Services":"Communication Services"
    }
    key=mapping.get(sector)
    etf=SECTOR_ETFS.get(key) if key else None
    if not etf: return None
    frame=sector_etf_history(etf)
    if frame is None or frame.empty or len(frame)<22: return None
    close=frame["Close"].dropna()
    stock=data.get("history")
    if stock is None or stock.empty: return None
    stock_close=stock["Close"].dropna()
    def ret(series,n):
        return (float(series.iloc[-1])/float(series.iloc[-n-1])-1)*100 if len(series)>n and float(series.iloc[-n-1]) else np.nan
    return {"sector":sector,"etf":etf,"one_month_stock":ret(stock_close,21),"one_month_etf":ret(close,21),
            "three_month_stock":ret(stock_close,63),"three_month_etf":ret(close,63)}


def thesis(data):
    i=data["info"]; t=data["technical"]; v=data["valuation"]; e=data["entries"]; sh=data["shield"]
    story=technical_story(t)
    st.markdown(f"## {company_name(data)} ({data['symbol']})")
    st.caption(f"{i.get('sector','Sector unavailable')} · {i.get('industry','Industry unavailable')} · {i.get('exchange','Exchange unavailable')}")
    a,b,c,d=st.columns(4)
    a.metric("Current price",money(t.get("price")))
    b.metric("1-month move",val(t.get("return_1m"),"%"))
    c.metric("3-month move",val(t.get("return_3m"),"%"))
    d.metric("RSI (14)",val(t.get("rsi")))
    st.markdown("### Price action — read the chart first")
    with st.expander("Chart display controls",expanded=True):
        x,y=st.columns(2); show_entry=x.checkbox("Show entry and risk levels",True,key=f"ent_{data['symbol']}");show_val=y.checkbox("Show valuation reference levels",False,key=f"val_{data['symbol']}")
    st.plotly_chart(build_chart(data,show_entry,show_val),use_container_width=True)
    st.markdown("### What the chart is telling us")
    st.markdown(f"**Trend:** {story['trend']}")
    st.markdown(f"**Momentum:** {story['momentum']}")
    st.markdown(f"**RSI:** {story['rsi']}")
    st.markdown(f"**Volume:** {story['volume']}")
    st.markdown(f"**Price structure:** {story['structure']}")
    st.markdown("### Key technical levels")
    level_rows=[
        ("20-day moving average",t.get("ma20")),("50-day moving average",t.get("ma50")),("200-day moving average",t.get("ma200")),
        ("Recent 20-day resistance",t.get("high20")),("Recent 20-day support",t.get("low20")),
        ("Early-entry zone",e.get("early_low")),("Pullback zone",e.get("pullback_low")),("Breakout confirmation",e.get("breakout")),
        ("Invalidation level",e.get("invalidation")),("Technical target 1",e.get("technical_target_1")),("Technical target 2",e.get("technical_target_2"))
    ]
    st.dataframe(pd.DataFrame([{"Level":k,"Price":money(x)} for k,x in level_rows]),use_container_width=True,hide_index=True)
    st.markdown("### The investment story")
    summary=i.get("longBusinessSummary")
    if summary: st.write(summary)
    else: st.caption("Company description was not returned by the data provider.")
    st.markdown("**Why it may deserve attention**")
    if data["news"]:
        for headline in data["news"][:8]: st.markdown(f"- {headline}")
    else: st.caption("No current headlines returned by the free news source. Check company filings and earnings updates before making a decision.")
    st.markdown("### Business quality — evidence, not a mystery score")
    m=data["fundamental_metrics"]
    metric_labels=[("Revenue growth","revenue_growth","%"),("Earnings growth","earnings_growth","%"),("Operating margin","operating_margin","%"),("Profit margin","profit_margin","%"),("Return on equity","roe","%"),("Free cash flow","fcf","$"),("Operating cash flow","operating_cash_flow","$"),("Debt / equity","debt_equity",""),("Forward P/E","forward_pe","x")]
    cols=st.columns(4)
    for idx,(label,key,suffix) in enumerate(metric_labels):
        x=m.get(key,np.nan); display=money(x) if suffix=="$" else (f"{x*100:.1f}%" if suffix=="%" and np.isfinite(x) else f"{x:.1f}{suffix}" if np.isfinite(x) else "N/A")
        cols[idx%4].metric(label,display)
    st.markdown("### What the financials actually say")
    for heading, explanation in fundamentals_story(m,i):
        st.markdown(f"**{heading}:** {explanation}")
    st.markdown("### Financial history — reported figures")
    financial_history=financial_history_frame(data)
    if not financial_history.empty:
        st.dataframe(financial_history,use_container_width=True)
        st.caption("Figures shown in billions, using periods returned by the free provider. Annual history may be shorter or unavailable; quarterly fallback is not annualized.")
    else:
        st.info("Historical statement rows were not returned for this company. Verify annual reports and filings before drawing conclusions.")
    st.markdown("### Industry and ETF context")
    relative=sector_relative_context(data)
    if relative:
        c1,c2=st.columns(2)
        c1.metric(f"{relative['etf']} · 1-month",f"{relative['one_month_etf']:+.1f}%")
        c2.metric("Company · 1-month",f"{relative['one_month_stock']:+.1f}%",f"{relative['one_month_stock']-relative['one_month_etf']:+.1f} pp vs sector ETF")
        c3,c4=st.columns(2)
        c3.metric(f"{relative['etf']} · 3-month",f"{relative['three_month_etf']:+.1f}%")
        c4.metric("Company · 3-month",f"{relative['three_month_stock']:+.1f}%",f"{relative['three_month_stock']-relative['three_month_etf']:+.1f} pp vs sector ETF")
        st.caption(f"Broad sector proxy: {relative['sector']} ({relative['etf']}). ETF performance is context, not a direct peer comparison.")
    else:
        st.caption("Sector ETF comparison unavailable for this classification or data pull.")
    chart_verdict, business_verdict = investment_readout(t,m,v,e)
    st.markdown("### Putting the chart and business together")
    st.info("**Chart read:** " + chart_verdict)
    st.info("**Business and valuation read:** " + business_verdict)
    status=m.get("fundamental_status","Insufficient data")
    available=int(m.get("metrics_available",0) or 0); expected=int(m.get("metrics_expected",0) or 0)
    if status=="Insufficient data":
        st.warning(f"Business quality is NOT RATED — only {available} of {expected} core metrics were retrieved. This is a data limitation, not proof of a weak business.")
    elif status=="Limited evidence":
        st.info(f"Business quality is PROVISIONAL — {available} of {expected} core metrics retrieved.")
    else:
        st.success(f"Financial evidence available — {available} of {expected} core metrics retrieved.")
    sources=m.get("metric_sources",{})
    with st.expander("Financial data sources and coverage"):
        source_rows=[]
        for label,key,suffix in metric_labels:
            x=m.get(key,np.nan)
            source_rows.append({"Metric":label,"Retrieved":bool(np.isfinite(x)),"Source":sources.get(key) or "Not returned by data provider"})
        st.dataframe(pd.DataFrame(source_rows),use_container_width=True,hide_index=True)
        if data.get("fundamental_data_errors"):st.caption("Provider retrieval notes: "+" · ".join(data["fundamental_data_errors"][:6]))
    st.markdown("### Valuation — what price might make sense?")
    st.caption("When available, these scenarios use published Wall Street analyst targets: low / mean / high. If analyst coverage is unavailable, the report falls back to a clearly labeled financial model.")
    x,y,z=st.columns(3)
    x.metric("Bear case · analyst low",money(v.get("bear")),val(v.get("bear_upside"),"%"))
    y.metric("Base case · analyst mean",money(v.get("base")),val(v.get("base_upside",v.get("fair_value_upside")),"%"))
    z.metric("Bull case · analyst high",money(v.get("bull")),val(v.get("bull_upside"),"%"))
    st.caption(v.get("valuation_note",""))
    st.metric("Base-case upside / downside",val(v.get("fair_value_upside"),"%"))
    st.caption("Valuation approach: " + str(v.get("valuation_method","Not available")))
    vi=v.get("valuation_inputs",{})
    valuation_rows=[]
    for label,key,fmt in [
        ("Current share price","current_price","money"),
        ("Analyst target low","analyst_target_low","money"),("Analyst target mean","analyst_target_mean","money"),
        ("Analyst target median","analyst_target_median","money"),("Analyst target high","analyst_target_high","money"),
        ("Number of analyst opinions","analyst_count","shares"),
        ("Forward EPS","forward_eps","money"),("Trailing EPS","trailing_eps","money"),
        ("Reported forward P/E","forward_pe_reported","multiple"),
        ("Reported price / sales","price_to_sales_reported","multiple"),("Revenue per share","revenue_per_share","money"),
        ("Reference P/E used","reference_pe","multiple"),("Reference price / sales used","reference_ps","multiple"),
        ("Revenue","revenue","money"),("Shares outstanding","shares_outstanding","shares")]:
        value=vi.get(key,np.nan)
        if isinstance(value,(int,float,np.number)) and np.isfinite(value):
            shown=money(value) if fmt=="money" else f"{value:,.0f}" if fmt=="shares" else f"{value:.1f}×"
            valuation_rows.append({"Valuation input":label,"Reported / assumed value":shown})
    if vi.get("sector") or vi.get("industry"):
        valuation_rows.append({"Valuation input":"Sector / industry","Reported / assumed value":f"{vi.get('sector','Not provided')} / {vi.get('industry','Not provided')}"})
    if valuation_rows:
        st.dataframe(pd.DataFrame(valuation_rows),use_container_width=True,hide_index=True)
    st.markdown("### Risk review")
    if sh["flags"]:
        for flag in sh["flags"]:st.warning(flag)
    else:st.success("No major screen-level risk flags. This is not a guarantee of safety or investment quality.")
    if sh["notes"]:
        for note in sh["notes"]:st.info(note)
    with st.expander("Model diagnostics and scores"):
        st.write({"Technical score":t.get("technical_score"),"Business quality score":data.get("fundamental_score"),"Opportunity rank":data.get("opportunity_score"),"Data coverage":data.get("fundamental_coverage")})
        st.caption("Scores are secondary diagnostics only. The chart, actual price levels, business evidence and valuation assumptions should drive the research decision.")
    st.caption("Research tool only. Free Yahoo Finance data may be delayed, incomplete or rate-limited. Technical levels are estimates, not guaranteed support or resistance.")

@st.cache_data(ttl=900,show_spinner=False)
def market_snapshot():
    symbols={"S&P 500":"SPY","Nasdaq 100":"QQQ","Russell 2000":"IWM","Dow":"DIA"};out={}
    for name,sym in symbols.items():
        h=history(sym,"6mo")
        if len(h)>22:
            c=h.Close;out[name]={"price":float(c.iloc[-1]),"1m":float((c.iloc[-1]/c.iloc[-22]-1)*100),"3m":float((c.iloc[-1]/c.iloc[-64]-1)*100) if len(c)>64 else np.nan}
    return out

def scan_market(count=DEFAULT_SCAN,mode="Investment"):
    candidates,coverage=discover_universe(count)
    progress=st.progress(0);status=st.empty();rows=[];total=min(len(candidates),count)
    for n,symbol in enumerate(candidates[:total]):
        status.caption(f"Researching {symbol} · {n+1}/{total}")
        try:
            d=research_company(symbol)
            if d:
                t=d["technical"];v=d["valuation"]
                chart_read = "Uptrend / constructive" if t.get("trend")=="Bullish" and t.get("return_1m",0)>0 else "Trying to improve" if t.get("trend")=="Improving" else "Weak / needs repair"
                row={"Ticker":symbol,"Company":company_name(d),"Price":t.get("price"),"1W Return":t.get("return_1w"),"1M Return":t.get("return_1m"),"3M Return":t.get("return_3m"),"RSI":t.get("rsi"),"Trend":t.get("trend"),"Chart Read":chart_read,"Opportunity Score":d.get("opportunity_score"),"Business Score":d.get("fundamental_score"),"Technical Score":t.get("technical_score"),"Momentum Score":t.get("momentum_score"),"Fundamental Coverage":d.get("fundamental_coverage"),"Fair Value Upside":v.get("fair_value_upside"),"Desk Flags":"; ".join(d["shield"]["flags"])}
                if mode=="Swing" and not (np.isfinite(t.get("price",np.nan)) and np.isfinite(t.get("ma20",np.nan)) and t["price"]>t["ma20"] and t.get("return_1m",0)>0 and t.get("relative_volume",0)>=0.8): continue
                rows.append(row)
        except Exception:pass
        progress.progress((n+1)/max(total,1))
    progress.empty();status.empty()
    rows.sort(key=lambda item: item.get("Opportunity Score") if np.isfinite(item.get("Opportunity Score",np.nan)) else -1, reverse=True)
    return rows,coverage


INDUSTRY_ETFS = {
    "Semiconductors":"SMH", "Software":"IGV", "Cybersecurity":"CIBR",
    "Biotechnology":"XBI", "Medical Devices":"IHI", "Robotics & Automation":"BOTZ",
    "Aerospace & Defense":"ITA", "Clean Energy":"ICLN", "Solar":"TAN",
    "Oil & Gas Exploration":"XOP", "Metals & Mining":"XME", "Regional Banks":"KRE",
    "Transportation":"IYT", "Retail":"XRT", "Homebuilders":"XHB",
    "Infrastructure":"PAVE", "Cloud Computing":"SKYY", "Fintech":"FINX",
    "Artificial Intelligence":"AIQ", "Uranium":"URA"
}

INDUSTRY_KEYWORDS = {
    "Semiconductors":["semiconductor","semiconductors","chip","integrated circuits"],
    "Software":["software","application software","systems software"],
    "Cybersecurity":["cybersecurity","security software","internet security"],
    "Biotechnology":["biotechnology","biotech"],
    "Medical Devices":["medical devices","medical instruments","healthcare equipment"],
    "Robotics & Automation":["robot","automation","industrial machinery"],
    "Aerospace & Defense":["aerospace","defense","military"],
    "Clean Energy":["renewable","clean energy","solar","wind"],
    "Solar":["solar"],
    "Oil & Gas Exploration":["oil & gas","oil and gas","exploration","drilling"],
    "Metals & Mining":["steel","copper","aluminum","gold","silver","mining"],
    "Regional Banks":["regional bank","regional banks"],
    "Transportation":["air freight","railroads","trucking","shipping","transportation"],
    "Retail":["retail","department stores","specialty stores"],
    "Homebuilders":["residential construction","homebuilding","home builders"],
    "Infrastructure":["engineering","construction","infrastructure"],
    "Cloud Computing":["cloud computing","software infrastructure"],
    "Fintech":["financial technology","credit services","capital markets"],
    "Artificial Intelligence":["artificial intelligence","AI software","technology"],
    "Uranium":["uranium"]
}


def industry_etf_snapshot():
    rows=[]
    benchmark=history("SPY","6mo")
    spy=benchmark["Close"].dropna() if benchmark is not None and not benchmark.empty else pd.Series(dtype=float)
    for theme,symbol in INDUSTRY_ETFS.items():
        frame=history(symbol,"6mo")
        if frame is None or frame.empty or len(frame)<22: continue
        close=frame["Close"].dropna()
        if len(close)<22: continue
        def pct(n):
            return (float(close.iloc[-1])/float(close.iloc[-n-1])-1)*100 if len(close)>n and close.iloc[-n-1] else np.nan
        one=pct(21); three=pct(63); week=pct(5)
        ma20=float(close.tail(20).mean()); ma50=float(close.tail(50).mean()) if len(close)>=50 else np.nan
        rsi=np.nan
        delta=close.diff()
        gains=delta.clip(lower=0).rolling(14).mean()
        losses=-delta.clip(upper=0).rolling(14).mean()
        if len(close)>=15 and losses.iloc[-1]>0:
            rsi=float(100-(100/(1+gains.iloc[-1]/losses.iloc[-1])))
        elif len(close)>=15 and gains.iloc[-1]>0 and losses.iloc[-1]==0:
            rsi=100.0
        spy_one=(float(spy.iloc[-1])/float(spy.iloc[-22])-1)*100 if len(spy)>22 and spy.iloc[-22] else np.nan
        spy_three=(float(spy.iloc[-1])/float(spy.iloc[-64])-1)*100 if len(spy)>64 and spy.iloc[-64] else np.nan
        rows.append({
            "Industry / theme":theme,"ETF":symbol,"Price":float(close.iloc[-1]),
            "1W Return":week,"1M Return":one,"3M Return":three,
            "1M vs SPY":one-spy_one if np.isfinite(spy_one) else np.nan,
            "3M vs SPY":three-spy_three if np.isfinite(spy_three) else np.nan,
            "Above 20D":bool(close.iloc[-1]>ma20),"Above 50D":bool(np.isfinite(ma50) and close.iloc[-1]>ma50),
            "RSI":rsi
        })
    return pd.DataFrame(rows)


def scan_industry_stocks(theme, scan_depth=100, max_reports=15):
    keywords=INDUSTRY_KEYWORDS.get(theme,[])
    candidates,coverage=discover_universe(scan_depth)
    matches=[]
    progress=st.progress(0);status=st.empty()
    total=min(len(candidates),scan_depth)
    for idx,symbol in enumerate(candidates[:total]):
        try:
            details=info(symbol)
            industry=str(details.get("industry","")).lower()
            sector=str(details.get("sector","")).lower()
            haystack=industry+" "+sector
            if keywords and any(word in haystack for word in keywords):
                matches.append({"symbol":symbol,"company":details.get("shortName") or details.get("longName") or symbol,"industry":details.get("industry","Unknown")})
        except Exception:
            pass
        progress.progress((idx+1)/max(total,1))
    progress.empty();status.empty()
    reports=[]
    progress=st.progress(0);status=st.empty()
    selected=matches[:max_reports]
    for idx,item in enumerate(selected):
        status.caption(f"Building company evidence · {item['symbol']} · {idx+1}/{len(selected)}")
        try:
            data=research_company(item["symbol"])
            if data:
                t=data["technical"]; v=data["valuation"]; entries=data["entries"]
                price=t.get("price",np.nan)
                pullback_low=entries.get("pullback_low",np.nan)
                distance=(price/pullback_low-1)*100 if np.isfinite(price) and np.isfinite(pullback_low) and pullback_low>0 else np.nan
                reports.append({
                    "Ticker":item["symbol"],"Company":company_name(data),"Industry":item["industry"],
                    "Price":price,"1M Return":t.get("return_1m"),"3M Return":t.get("return_3m"),
                    "Trend":t.get("trend"),"RSI":t.get("rsi"),"Technical Score":t.get("technical_score"),
                    "Business Score":data.get("fundamental_score"),"Opportunity Score":data.get("opportunity_score"),
                    "Fair Value Upside":v.get("fair_value_upside"),"Distance vs Pullback Zone":distance,
                    "Desk Flags":"; ".join(data["shield"]["flags"])
                })
        except Exception:
            pass
        progress.progress((idx+1)/max(len(selected),1))
    progress.empty();status.empty()
    reports.sort(key=lambda row: row.get("Opportunity Score") if np.isfinite(row.get("Opportunity Score",np.nan)) else -1,reverse=True)
    return reports,coverage,len(matches)


def render_industry_discovery():
    st.markdown("## Industry & ETF Discovery")
    st.write("Find where capital is moving, compare industry trends with the S&P 500, then inspect individual companies for business quality and early entry setups.")
    st.caption("Industry ETFs are investable proxies, not pure measures of every company in a theme. ETF performance can be concentrated in a few large holdings.")
    if st.button("Refresh industry leadership",type="primary"):
        st.cache_data.clear()
        st.session_state.pop("industry_snapshot",None)
    if "industry_snapshot" not in st.session_state:
        with st.spinner("Comparing industry ETFs with the market..."):
            st.session_state["industry_snapshot"]=industry_etf_snapshot()
    frame=st.session_state["industry_snapshot"]
    if frame.empty:
        st.warning("Industry ETF price history is unavailable from the free data source right now.")
        return
    frame=frame.sort_values(["1M vs SPY","3M vs SPY"],ascending=False,na_position="last")
    st.markdown("### Industry leadership")
    st.dataframe(frame,use_container_width=True,hide_index=True,column_config={
        "Price":st.column_config.NumberColumn(format="$%.2f"),
        "1W Return":st.column_config.NumberColumn(format="%.1f%%"),
        "1M Return":st.column_config.NumberColumn(format="%.1f%%"),
        "3M Return":st.column_config.NumberColumn(format="%.1f%%"),
        "1M vs SPY":st.column_config.NumberColumn(format="%+.1f pp"),
        "3M vs SPY":st.column_config.NumberColumn(format="%+.1f pp"),
        "RSI":st.column_config.NumberColumn(format="%.1f")
    })
    st.caption("Relative returns are percentage-point differences versus SPY over matching lookback windows. RSI and moving-average flags describe the ETF chart, not its holdings.")
    st.markdown("### Find individual companies in a leading theme")
    theme=st.selectbox("Choose an industry or theme",list(INDUSTRY_ETFS.keys()),index=0)
    etf=INDUSTRY_ETFS[theme]
    etf_row=frame[frame["ETF"]==etf]
    if not etf_row.empty:
        row=etf_row.iloc[0]
        st.write(f"**{theme} ({etf})** · 1M {row['1M Return']:+.1f}% · 3M {row['3M Return']:+.1f}% · vs SPY {row['1M vs SPY']:+.1f} percentage points over one month.")
        if not (row["Above 20D"] and row["Above 50D"]):
            st.info("The ETF trend is not above both its 20- and 50-day averages. Treat the theme as developing or weak until the chart improves.")
    depth=st.select_slider("Candidate universe to inspect",options=[40,60,80,100,125,150],value=80,key="industry_depth")
    if st.button("Find companies in this industry",type="primary"):
        with st.spinner(f"Matching listed companies to {theme}, then evaluating fundamentals and technicals..."):
            reports,coverage,match_count=scan_industry_stocks(theme,depth)
        st.session_state["industry_reports"]=reports
        st.session_state["industry_coverage"]=coverage
        st.session_state["industry_match_count"]=match_count
        st.session_state["industry_selected_theme"]=theme
    reports=st.session_state.get("industry_reports",[])
    if reports and st.session_state.get("industry_selected_theme")==theme:
        st.caption(f"Matched {st.session_state.get('industry_match_count',0)} candidate descriptions in a sampled universe. Fully researched {len(reports)}. Candidate source: {st.session_state.get('industry_coverage',{})}.")
        columns=["Ticker","Company","Industry","Price","1M Return","3M Return","Trend","RSI","Technical Score","Business Score","Opportunity Score","Fair Value Upside","Distance vs Pullback Zone","Desk Flags"]
        st.dataframe(pd.DataFrame(reports)[columns],use_container_width=True,hide_index=True,column_config={
            "Price":st.column_config.NumberColumn(format="$%.2f"),
            "1M Return":st.column_config.NumberColumn(format="%.1f%%"),
            "3M Return":st.column_config.NumberColumn(format="%.1f%%"),
            "RSI":st.column_config.NumberColumn(format="%.1f"),
            "Technical Score":st.column_config.NumberColumn(format="%.1f"),
            "Business Score":st.column_config.NumberColumn(format="%.1f"),
            "Opportunity Score":st.column_config.NumberColumn(format="%.1f"),
            "Fair Value Upside":st.column_config.NumberColumn(format="%.1f%%"),
            "Distance vs Pullback Zone":st.column_config.NumberColumn(format="%.1f%%")
        })
        pick=st.selectbox("Open full company report",[x["Ticker"] for x in reports],key="industry_pick")
        if st.button("Build full investment report",key="industry_full_report"):
            report=research_company(pick)
            if report:
                st.session_state["active_report"]=report
                record_research(report)
        if st.session_state.get("active_report"):
            thesis(st.session_state["active_report"])
    elif st.session_state.get("industry_selected_theme")==theme:
        st.info("No matching companies with complete research data were found in this sampled candidate pool. Try a larger universe or another theme.")
    st.caption("Free Yahoo Finance industry classifications can be broad or missing. This scan is a discovery sample, not a complete ETF holdings look-through or exhaustive exchange scan. Confirm holdings and business exposure before relying on a theme match.")



if page=="Command Center":
    st.markdown("## Investment Command Center")
    st.write("A concise view of market conditions and the research priorities most deserving of your attention.")
    snapshot=market_snapshot(); cols=st.columns(4)
    for col,(name,d) in zip(cols,snapshot.items()):col.metric(name,money(d["price"]),f"1M {d['1m']:+.2f}%")
    st.markdown("### Sector leadership")
    sectors=[]
    for name,sym in SECTOR_ETFS.items():
        h=sector_etf_history(sym)
        if len(h)>22:
            c=h.Close;sectors.append({"Sector":name,"1M Return":(c.iloc[-1]/c.iloc[-22]-1)*100,"3M Return":(c.iloc[-1]/c.iloc[-64]-1)*100 if len(c)>64 else np.nan})
    if sectors:st.dataframe(pd.DataFrame(sectors).sort_values("1M Return",ascending=False),use_container_width=True,hide_index=True)
    st.markdown("### Today's research priorities")
    st.caption("Run a fresh discovery scan to identify companies worth deeper investigation.")
    count=st.select_slider("Initial scan depth",options=[25,40,60,80,100,125,150],value=DEFAULT_SCAN)
    if st.button("Run investment intelligence scan",type="primary"):
        with st.spinner("Scout is discovering candidates; specialist engines are evaluating them..."):
            rows,cov=scan_market(count)
        st.session_state["command_rows"]=rows;st.session_state["scan_coverage"]=cov
    rows=st.session_state.get("command_rows",[])
    if rows:
        st.caption(f"Dynamic candidate pool: {st.session_state.get('scan_coverage',{})}. Results are a sampled screen, not exhaustive coverage of every listing.")
        research_table(rows)
        pick=st.selectbox("Open investment report",[r["Ticker"] for r in rows],key="cmd_pick")
        if st.button("Build full report",key="cmd_report"):
            d=research_company(pick);st.session_state["active_report"]=d
        if st.session_state.get("active_report"):thesis(st.session_state["active_report"])
    else:st.info("Run the intelligence scan to populate your research priorities.")

elif page=="Industry & ETF Discovery":
    render_industry_discovery()

elif page=="Market Opportunities":
    st.markdown("## Market Opportunities")
    st.write("Discover companies, then inspect the actual chart, business fundamentals and valuation. The scan is a starting point—not a score-based verdict.")
    count=st.select_slider("Companies to evaluate",options=[25,40,60,80,100,125,150],value=DEFAULT_SCAN,key="opp_count")
    if st.button("Discover opportunities",type="primary"):
        with st.spinner("Evaluating dynamic market candidates..."):rows,cov=scan_market(count)
        st.session_state["opp_rows"]=rows;st.session_state["opp_cov"]=cov
    rows=st.session_state.get("opp_rows",[])
    if rows:
        st.caption(f"Candidate-source coverage: {st.session_state.get('opp_cov',{})}")
        research_table(rows)
        pick=st.selectbox("Select a company for deeper research",[r["Ticker"] for r in rows],key="opp_pick")
        if st.button("Research selected company",type="primary"):
            d=research_company(pick);st.session_state["active_report"]=d;record_research(d)
        if st.session_state.get("active_report"):thesis(st.session_state["active_report"])

elif page=="Company Research":
    st.markdown("## Company Research")
    with st.form("company_form"):
        ticker=st.text_input("Enter any listed ticker",placeholder="e.g. NVDA, MU, COST, SOFI").strip().upper()
        go=st.form_submit_button("Build investment report",type="primary")
    if go:
        with st.spinner(f"Researching {ticker}..."):
            d=research_company(ticker)
        if d:st.session_state["active_report"]=d;record_research(d)
        else:st.error("Could not retrieve sufficient price history. Verify ticker and try again.")
    if st.session_state.get("active_report"):thesis(st.session_state["active_report"])

elif page=="Entry & Risk":
    st.markdown("## Entry & Risk Intelligence")
    st.write("Evaluate whether a promising company is approaching an attractive price—or whether the setup is already extended.")
    ticker=st.text_input("Ticker to analyze",placeholder="Enter a ticker",key="entry_ticker").strip().upper()
    if st.button("Analyze entry and risk",type="primary") and ticker:
        d=research_company(ticker)
        if d:st.session_state["entry_report"]=d;record_research(d)
    if st.session_state.get("entry_report"):thesis(st.session_state["entry_report"])

elif page=="Swing Research":
    st.markdown("## Swing Research")
    st.write("A separate short-horizon view focused on trend, momentum, volume and price structure. It does not replace long-term business analysis.")
    count=st.select_slider("Scan depth",options=[25,40,60,80,100],value=40,key="swing_depth")
    if st.button("Scan swing setups",type="primary"):
        with st.spinner("Screening short-term technical conditions..."):rows,cov=scan_market(count,"Swing")
        st.session_state["swing_rows"]=rows
    rows=st.session_state.get("swing_rows",[])
    if rows:
        research_table(rows)
        pick=st.selectbox("Inspect swing setup",[r["Ticker"] for r in rows],key="swing_pick")
        if st.button("Open swing research"):
            d=research_company(pick);st.session_state["active_report"]=d
        if st.session_state.get("active_report"):thesis(st.session_state["active_report"])
    else:st.info("Run the swing scan to identify current setups.")

elif page=="AI Investment Committee":
    st.markdown("## AI Investment Committee")
    st.write("A coordinated research review. Each specialist evaluates the same company data, then the coordinator reconciles the evidence.")
    ticker=st.text_input("Company ticker",placeholder="NVDA, MU, AMD, AMZN, SOFI",key="committee_ticker").strip().upper()
    if st.button("Convene investment committee",type="primary") and ticker:
        with st.spinner("Collecting shared market, financial, valuation and technical evidence..."):
            d=research_company(ticker)
        if d:
            st.session_state["committee_report"]=d
            record_research(d)
        else:
            st.error("Insufficient price history returned for this ticker.")
    d=st.session_state.get("committee_report")
    if d:
        c=run_committee(d); t=d["technical"]; v=d["valuation"]
        st.markdown("---")
        st.markdown(f"### {d['symbol']} · Committee verdict")
        st.subheader(c["verdict"])
        cols=st.columns(4)
        cols[0].metric("Last price",money(t.get("price")))
        cols[1].metric("Technical score",val(t.get("technical_score"),"/100"))
        cols[2].metric("Business score",val(d.get("fundamental_score"),"/100"))
        cols[3].metric("Base reference",money(v.get("base")),val(v.get("fair_value_upside"),"%"))
        st.caption("Scores are diagnostics, not probabilities of success.")
        st.markdown("### Specialist reports")
        for name, finding in c["agents"]:
            with st.expander(name,expanded=True):
                st.write(finding)
        st.markdown("### Entry map")
        level_cols=st.columns(4)
        for idx,(label,value) in enumerate(c["levels"].items()):
            level_cols[idx%4].metric(label,money(value))
        st.markdown("### Coordinator's decision")
        st.info("The committee does not force a buy signal. Conflicting evidence, missing fundamentals or an extended chart should lead to a wait.")
        st.caption(c["limitations"])
        if st.button("Refresh committee analysis"):
            st.cache_data.clear()
            st.rerun()

elif page=="Institutional Research Suite":
    render_research_suite()

elif page=="Research History":
    st.markdown("## Research History")
    st.write("A record of companies researched in this deployment. Streamlit Cloud local storage may reset on redeploy or restart; export records if you need durable storage.")
    df=log_frame()
    if df.empty:st.info("No research records yet. Build company reports to start a history.")
    else:
        st.dataframe(df.sort_values("timestamp",ascending=False),use_container_width=True,hide_index=True)
        st.download_button("Download research history CSV",df.to_csv(index=False).encode(),"research_history.csv","text/csv")

else:
    st.markdown("## Research Methodology")
    st.markdown("### Independent research engines")
    st.write("Market Scout discovers candidates through Yahoo Finance screeners and a rotating sample of public exchange symbol directories. Business Quality scores reported growth, margins, returns, free cash flow, leverage and valuation inputs. Technical Intelligence scores trend, momentum, RSI, volume and price structure. Valuation uses a sector-reference P/E when positive forward or trailing EPS is available, and falls back to a transparent sector-reference price-to-sales scenario when earnings are unavailable. Scenario multiples are assumptions, not analyst targets. Shield highlights data gaps and screen-level risks.")
    st.markdown("### How to read a company report")
    st.write("Start with the candlestick chart and moving averages. Read trend, momentum, RSI, relative volume, support, resistance and invalidation together. Then inspect revenue and earnings growth, margins, cash generation, leverage and valuation. The final readout explains where the chart and business agree—or disagree. Screening scores are not investment conclusions.")
    st.markdown("### Important limitations")
    st.write("This is a research and education tool, not individualized financial advice. Yahoo Finance data can be delayed, incomplete, rate-limited or changed without notice. Dynamic exchange-directory sampling is not an exhaustive real-time scan. Financial metrics are not independently audited here. Bull/base/bear scenarios are sensitivity estimates, not price forecasts. No orders are placed and no brokerage is connected.")
    st.markdown("### What the system does not do")
    st.write("It does not promise returns, infer undisclosed information, execute trades, or claim that a high score guarantees a good investment. Always verify financial statements, valuation assumptions, earnings dates and material news from primary sources.")
