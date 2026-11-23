import numpy as np
from data.market_data import history, info, news
from engines.analysis_engines import technical_engine, fundamental_engine, valuation_engine, entry_engine, shield_engine, opportunity_score, fnum

def research_company(symbol):
    symbol=str(symbol).strip().upper()
    h=history(symbol,"2y")
    if h is None or h.empty or len(h)<40: return None
    i=info(symbol); t=technical_engine(h); metrics,fund,coverage=fundamental_engine(i)
    val=valuation_engine(i,t.get("price",np.nan)); val["fair_value_upside"]=(val["fair_value"]/t["price"]-1)*100 if np.isfinite(val["fair_value"]) and t.get("price",0)>0 else np.nan
    entries=entry_engine(t); shield=shield_engine(fund,t.get("technical_score",np.nan),val,entries,i)
    n=news(symbol)
    catalyst_score=55
    headlines=[]
    for item in n[:12]:
        content=item.get("content",item) if isinstance(item,dict) else {}
        title=content.get("title","") if isinstance(content,dict) else ""
        if title: headlines.append(title)
    joined=" ".join(headlines).lower()
    if any(x in joined for x in ["raises guidance","beats estimates","record revenue","upgrade"]): catalyst_score=75
    if any(x in joined for x in ["cuts guidance","misses estimates","investigation","downgrade"]): catalyst_score=30
    score=opportunity_score(fund,t.get("technical_score",np.nan),val["fair_value_upside"],catalyst_score)
    return {"symbol":symbol,"history":h,"info":i,"technical":t,"fundamental_metrics":metrics,"fundamental_score":fund,"fundamental_coverage":coverage,"valuation":val,"entries":entries,"shield":shield,"news":headlines,"catalyst_score":catalyst_score,"opportunity_score":score}
