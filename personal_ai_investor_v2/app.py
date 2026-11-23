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
:root{color-scheme:light}.stApp{background:#f3f5f4;color:#202a25}.block-container{max-width:1500px;padding-top:1.3rem;padding-bottom:3rem}
[data-testid="stSidebar"]{background:#fff;border-right:1px solid #e1e7e3}.hero{background:linear-gradient(115deg,#fff 0%,#f5faf7 100%);border:1px solid #dce6df;border-radius:16px;padding:1.5rem 1.7rem;margin-bottom:1.2rem}
.kicker{font-size:.7rem;letter-spacing:.16em;font-weight:800;color:#47725d;text-transform:uppercase}.hero h1{font-size:2rem;line-height:1.15;margin:.35rem 0;color:#1f2d25}.hero p{color:#68766e;margin:0}.panel{background:#fff;border:1px solid #e1e7e3;border-radius:12px;padding:1rem 1.1rem}
div[data-testid="stMetric"]{background:#fff;border:1px solid #e1e7e3;padding:.8rem;border-radius:10px} .stButton>button{border-radius:8px;font-weight:700;border:1px solid #cbd8d0}.stButton>button[kind="primary"]{background:#315f4b;color:white;border-color:#315f4b}
[data-testid="stDataFrame"]{border:1px solid #e1e7e3;border-radius:10px;overflow:hidden}hr{border-color:#e1e7e3}
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
    df=pd.DataFrame(rows).sort_values("Opportunity Rank",ascending=False)
    st.dataframe(df,use_container_width=True,hide_index=True,height=min(560,42+35*min(len(df),14)),column_config={"Opportunity Rank":st.column_config.ProgressColumn(min_value=0,max_value=100),"Business Quality":st.column_config.ProgressColumn(min_value=0,max_value=100),"Technical Strength":st.column_config.ProgressColumn(min_value=0,max_value=100),"Data Coverage":st.column_config.ProgressColumn(min_value=0,max_value=100),"Price":st.column_config.NumberColumn(format="$%.2f"),"Fair Value Upside":st.column_config.NumberColumn(format="%.1f%%")})

def thesis(data):
    i=data["info"]; t=data["technical"]; v=data["valuation"]; e=data["entries"]; sh=data["shield"]
    st.markdown(f"## {company_name(data)} ({data['symbol']})")
    st.caption(f"{i.get('sector','Sector unavailable')} · {i.get('industry','Industry unavailable')} · {i.get('exchange','Exchange unavailable')}")
    a,b,c,d=st.columns(4); a.metric("Opportunity rank",val(data["opportunity_score"]));b.metric("Business quality",val(data["fundamental_score"]));c.metric("Technical strength",val(t.get("technical_score")));d.metric("Data coverage",val(data["fundamental_coverage"],"%"))
    st.markdown("### Investment desk conclusion")
    if sh["flags"]: st.warning("Shield review: " + " · ".join(sh["flags"]))
    else: st.success("No major screen-level risk flags. This is not a guarantee of safety or investment quality.")
    if data["fundamental_score"]>=70 and t.get("technical_score",0)>=65 and (not np.isfinite(v.get("fair_value_upside",np.nan)) or v["fair_value_upside"]>0):
        st.markdown("**Desk view:** Business and chart evidence are constructive. Check the valuation assumptions and entry levels before considering an investment.")
    elif data["fundamental_score"]>=65 and t.get("technical_score",0)<55:
        st.markdown("**Desk view:** Business quality may justify further research, but the chart is not yet confirming. Patience may offer a better entry.")
    elif t.get("technical_score",0)>=70 and (not np.isfinite(data["fundamental_score"]) or data["fundamental_score"]<55):
        st.markdown("**Desk view:** Technical interest is present, but business quality or data coverage needs more work. Treat as speculative until verified.")
    else: st.markdown("**Desk view:** Mixed evidence. Keep on research radar only if the underlying thesis interests you; do not force an entry.")
    st.markdown("### Business and financial evidence")
    m=data["fundamental_metrics"]
    metric_labels=[("Revenue growth","revenue_growth","%"),("Earnings growth","earnings_growth","%"),("Operating margin","operating_margin","%"),("Profit margin","profit_margin","%"),("Return on equity","roe","%"),("Free cash flow","fcf","$"),("Debt / equity","debt_equity",""),("Forward P/E","forward_pe","x")]
    cols=st.columns(4)
    for idx,(label,key,suffix) in enumerate(metric_labels):
        x=m.get(key,np.nan); display=money(x) if suffix=="$" else (f"{x*100:.1f}%" if suffix=="%" and np.isfinite(x) else f"{x:.1f}{suffix}" if np.isfinite(x) else "N/A")
        cols[idx%4].metric(label,display)
    if data["fundamental_coverage"]<55: st.warning("Limited financial data coverage. Missing values are not treated as zero; verify filings before relying on the business score.")
    st.markdown("### Technical intelligence")
    st.write(f"**Trend:** {t.get('trend','N/A')} · **Momentum score:** {val(t.get('momentum_score'))} · **RSI:** {val(t.get('rsi'))} · **Relative volume:** {val(t.get('relative_volume'),'x')}")
    with st.expander("Chart display controls",expanded=True):
        x,y=st.columns(2); show_entry=x.checkbox("Show technical entry levels",True,key=f"ent_{data['symbol']}");show_val=y.checkbox("Show bull/base/bear valuation overlays",False,key=f"val_{data['symbol']}")
    st.plotly_chart(build_chart(data,show_entry,show_val),use_container_width=True)
    st.markdown("### Entry plan")
    entry_rows=[("Early entry",e.get("early_low"),e.get("early_high")),("Pullback entry",e.get("pullback_low"),e.get("pullback_high")),("Breakout confirmation",e.get("breakout"),None),("Invalidation",e.get("invalidation"),None),("Technical target 1",e.get("technical_target_1"),None),("Technical target 2",e.get("technical_target_2"),None)]
    st.dataframe(pd.DataFrame([{"Level":k,"Price / Low":money(a),"High":money(b) if b is not None else "—"} for k,a,b in entry_rows]),use_container_width=True,hide_index=True)
    st.markdown("### Valuation scenarios")
    x,y,z=st.columns(3);x.metric("Bear case",money(v.get("bear")));y.metric("Base case / fair value",money(v.get("base")));z.metric("Bull case",money(v.get("bull")))
    st.caption(v.get("valuation_note",""))
    st.metric("Fair-value upside / downside",val(v.get("fair_value_upside"),"%"))
    st.markdown("### Catalysts and potential risks")
    if data["news"]:
        for headline in data["news"][:8]: st.markdown(f"- {headline}")
    else: st.caption("No current headlines returned by the free news source.")
    if sh["notes"]:
        for note in sh["notes"]: st.warning(note)
    summary=i.get("longBusinessSummary")
    if summary:
        with st.expander("Company business description"):st.write(summary)
    st.caption("Scores are transparent screening estimates, not predictions. Simplified forward-EPS valuation is not a discounted cash-flow model or analyst consensus.")

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
                row={"Ticker":symbol,"Company":company_name(d),"Opportunity Rank":d["opportunity_score"],"Business Quality":d["fundamental_score"],"Technical Strength":t.get("technical_score"),"Data Coverage":d["fundamental_coverage"],"Price":t.get("price"),"Fair Value Upside":v.get("fair_value_upside"),"1M Return":t.get("return_1m"),"RSI":t.get("rsi"),"Trend":t.get("trend"),"Desk Flags":"; ".join(d["shield"]["flags"])}
                if mode=="Swing" and (t.get("technical_score",0)<55): continue
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
    st.write("Discover across sectors, then rank companies using business quality, technical structure, valuation and catalyst context.")
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
    st.markdown("## Scoring & Methodology")
    st.markdown("### Independent research engines")
    st.write("Market Scout discovers candidates through Yahoo Finance screeners and a rotating sample of public exchange symbol directories. Business Quality scores reported growth, margins, returns, free cash flow, leverage and valuation inputs. Technical Intelligence scores trend, momentum, RSI, volume and price structure. Valuation uses a simplified forward-EPS multiple model when data permits. Shield highlights data gaps and screen-level risks.")
    st.markdown("### Opportunity Rank")
    st.write("Starting weights: Business Quality 35%, Technical Strength 35%, Valuation Attractiveness 20%, Catalyst Context 10%. When a component is unavailable, the rank renormalizes the available weights. Missing data affects confidence and is displayed separately; it is not silently treated as zero.")
    st.markdown("### Important limitations")
    st.write("This is a research and education tool, not individualized financial advice. Yahoo Finance data can be delayed, incomplete, rate-limited or changed without notice. Dynamic exchange-directory sampling is not an exhaustive real-time scan. Financial metrics are not independently audited here. Bull/base/bear scenarios are sensitivity estimates, not price forecasts. No orders are placed and no brokerage is connected.")
    st.markdown("### What the system does not do")
    st.write("It does not promise returns, infer undisclosed information, execute trades, or claim that a high score guarantees a good investment. Always verify financial statements, valuation assumptions, earnings dates and material news from primary sources.")
