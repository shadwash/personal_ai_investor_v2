import numpy as np

def _num(x):
    try:
        x=float(x)
        return x if np.isfinite(x) else np.nan
    except (TypeError,ValueError):
        return np.nan

def run_committee(report):
    """Five deterministic specialist agents using the app's shared research payload."""
    t=report.get("technical",{}); m=report.get("fundamental_metrics",{})
    v=report.get("valuation",{}); e=report.get("entries",{}); sh=report.get("shield",{})
    price=_num(t.get("price")); tech=_num(t.get("technical_score"))
    fund=_num(report.get("fundamental_score")); upside=_num(v.get("fair_value_upside"))
    rsi=_num(t.get("rsi")); relvol=_num(t.get("relative_volume"))
    rev=_num(m.get("revenue_growth")); earn=_num(m.get("earnings_growth")); fcf=_num(m.get("fcf"))
    ma20=_num(t.get("ma20")); ma50=_num(t.get("ma50")); ma200=_num(t.get("ma200"))
    # Scout: candidate discovery from price action + catalyst evidence.
    scout_score=np.nanmean([tech, _num(report.get("catalyst_score"))]) if np.isfinite(tech) else _num(report.get("catalyst_score"))
    scout=("Interesting activity: momentum/technical evidence or news catalysts warrant deeper review." if np.isfinite(scout_score) and scout_score>=65 else "No strong discovery signal yet; keep on the radar rather than forcing a trade.")
    # Fundamental analyst.
    analyst=("Business evidence is encouraging: reported growth and positive cash generation are present." if np.isfinite(rev) and rev>0 and np.isfinite(fcf) and fcf>0 else "Business quality is mixed or incomplete. Review reported growth, margins, cash generation and leverage before upgrading conviction.")
    if not np.isfinite(fund): analyst="NOT RATED: insufficient reported fundamental metrics. Missing data is not a negative score."
    # Technician.
    aligned=all(np.isfinite(x) for x in [price,ma20,ma50,ma200]) and price>ma20>ma50>ma200
    extended=np.isfinite(rsi) and rsi>=70
    technician=("Bullish moving-average alignment; assess pullback levels before entry." if aligned else "Trend is not fully aligned; wait for a reclaim/hold of key moving averages." )
    if extended: technician += " RSI is elevated; avoid chasing strength."
    if np.isfinite(relvol) and relvol>=1.5: technician += " Elevated relative volume: confirm whether it accompanies accumulation or selling."
    # Pilot: honest historical-data gate; don't fabricate a backtest.
    pilot="No strategy backtest has been run in this committee pass. Treat the setup as unvalidated until the Strategy Lab tests explicit entry/exit rules against historical data."
    # Shield.
    risks=list(sh.get("flags",[]))+list(sh.get("notes",[]))
    if np.isfinite(upside) and upside<0: risks.append("Valuation reference implies downside from the current price.")
    if not np.isfinite(upside): risks.append("No defensible valuation reference returned; upside is unknown.")
    if not np.isfinite(fund): risks.append("Fundamental data coverage is insufficient.")
    shield="; ".join(dict.fromkeys(risks)) if risks else "No major screen-level flags returned. This does not establish that the investment is safe."
    # Coordinator: conservative decision rules.
    if not np.isfinite(price) or not np.isfinite(tech):
        verdict="INSUFFICIENT DATA"
    elif np.isfinite(fund) and fund>=65 and tech>=65 and np.isfinite(upside) and upside>=15 and not extended and not risks:
        verdict="HIGH-QUALITY SETUP — CHECK ENTRY"
    elif tech>=60 and (not np.isfinite(fund) or fund<65):
        verdict="WATCH — BUSINESS EVIDENCE NEEDED"
    elif tech>=60 and np.isfinite(upside) and upside<0:
        verdict="WAIT — PRICE / VALUATION CONFLICT"
    elif extended:
        verdict="DO NOT CHASE — WAIT FOR RESET"
    else:
        verdict="WAIT FOR BETTER CONFIRMATION"
    return {
      "scores":{"Scout":scout_score,"Business Analyst":fund,"Technician":tech,"Coordinator Opportunity":_num(report.get("opportunity_score"))},
      "agents":[("SCOUT",scout),("BUSINESS ANALYST",analyst),("TECHNICIAN",technician),("PILOT",pilot),("SHIELD",shield)],
      "verdict":verdict,
      "levels":{"Early entry low":_num(e.get("early_low")),"Early entry high":_num(e.get("early_high")),"Pullback low":_num(e.get("pullback_low")),"Pullback high":_num(e.get("pullback_high")),"Breakout trigger":_num(e.get("breakout")),"Invalidation":_num(e.get("invalidation")),"Analyst/base reference":_num(v.get("base"))},
      "limitations":"These are transparent rule-based specialist engines, not five independent LLMs. No trade execution. Data may be delayed or incomplete; price targets are analyst consensus when labeled as such or model scenarios otherwise."
    }
