import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import numpy as np
import pandas as pd
import streamlit as st
from config import APP_NAME, APP_TAGLINE, DEFAULT_SCAN, MAX_SCAN, SECTOR_ETFS
from data.market_data import discover_universe, history, sector_etf_history
from research.company_research import research_company
from charts.price_chart import build_chart
from storage.history import record_research, log_frame

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
@media(max-width:700px){.hero{padding:1.25rem}.hero h1{font-size:1.65rem}.block-container{padding-left:1rem;padding-right:1rem}}
</style>
<div class="hero"><div class="kicker">Independent research desk · Version 2.0</div><h1>PERSONAL AI INVESTOR</h1><p>Discover exceptional businesses. Challenge the evidence. Find attractive prices before chasing becomes the only option.</p></div>
""",unsafe_allow_html=True)

PAGES=["Command Center","Market Opportunities","Company Research","Entry & Risk","Swing Research","Research History","Methodology"]
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
    preferred=["Ticker","Company","Price","1W Return","1M Return","3M Return","RSI","Trend","Chart Read","Fair Value Upside","Desk Flags"]
    df=df[[c for c in preferred if c in df.columns]]
    st.dataframe(df,use_container_width=True,hide_index=True,height=min(560,42+35*min(len(df),14)),column_config={"Price":st.column_config.NumberColumn(format="$%.2f"),"1W Return":st.column_config.NumberColumn(format="%.1f%%"),"1M Return":st.column_config.NumberColumn(format="%.1f%%"),"3M Return":st.column_config.NumberColumn(format="%.1f%%"),"RSI":st.column_config.NumberColumn(format="%.1f"),"Fair Value Upside":st.column_config.NumberColumn(format="%.1f%%")})


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
    x,y,z=st.columns(3);x.metric("Bear case",money(v.get("bear")));y.metric("Base case",money(v.get("base")));z.metric("Bull case",money(v.get("bull")))
    st.caption(v.get("valuation_note",""))
    st.metric("Fair-value upside / downside",val(v.get("fair_value_upside"),"%"))
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
                row={"Ticker":symbol,"Company":company_name(d),"Price":t.get("price"),"1W Return":t.get("return_1w"),"1M Return":t.get("return_1m"),"3M Return":t.get("return_3m"),"RSI":t.get("rsi"),"Trend":t.get("trend"),"Chart Read":chart_read,"Fair Value Upside":v.get("fair_value_upside"),"Desk Flags":"; ".join(d["shield"]["flags"])}
                if mode=="Swing" and not (np.isfinite(t.get("price",np.nan)) and np.isfinite(t.get("ma20",np.nan)) and t["price"]>t["ma20"] and t.get("return_1m",0)>0 and t.get("relative_volume",0)>=0.8): continue
                rows.append(row)
        except Exception:pass
        progress.progress((n+1)/max(total,1))
    progress.empty();status.empty()
    return rows,coverage

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
    st.write("Market Scout discovers candidates through Yahoo Finance screeners and a rotating sample of public exchange symbol directories. Business Quality scores reported growth, margins, returns, free cash flow, leverage and valuation inputs. Technical Intelligence scores trend, momentum, RSI, volume and price structure. Valuation uses a simplified forward-EPS multiple model when data permits. Shield highlights data gaps and screen-level risks.")
    st.markdown("### How to read a company report")
    st.write("Start with the candlestick chart and moving averages. Read trend, momentum, RSI, relative volume, support, resistance and invalidation together. Then inspect revenue and earnings growth, margins, cash generation, leverage and valuation. The final readout explains where the chart and business agree—or disagree. Screening scores are not investment conclusions.")
    st.markdown("### Important limitations")
    st.write("This is a research and education tool, not individualized financial advice. Yahoo Finance data can be delayed, incomplete, rate-limited or changed without notice. Dynamic exchange-directory sampling is not an exhaustive real-time scan. Financial metrics are not independently audited here. Bull/base/bear scenarios are sensitivity estimates, not price forecasts. No orders are placed and no brokerage is connected.")
    st.markdown("### What the system does not do")
    st.write("It does not promise returns, infer undisclosed information, execute trades, or claim that a high score guarantees a good investment. Always verify financial statements, valuation assumptions, earnings dates and material news from primary sources.")
