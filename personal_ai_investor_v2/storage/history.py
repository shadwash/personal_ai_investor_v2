import json
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd

STORE=Path(__file__).resolve().parent/"research_log.json"

def load_log():
    try:
        if STORE.exists(): return json.loads(STORE.read_text())
    except Exception: pass
    return []

def record_research(data):
    log=load_log(); t=data.get("technical",{}); v=data.get("valuation",{})
    log.append({"timestamp":datetime.now(timezone.utc).isoformat(),"symbol":data["symbol"],"price":t.get("price"),"opportunity_score":data.get("opportunity_score"),"fundamental_score":data.get("fundamental_score"),"technical_score":t.get("technical_score"),"fair_value":v.get("fair_value")})
    STORE.write_text(json.dumps(log[-2000:],indent=2,default=str))

def log_frame():
    return pd.DataFrame(load_log())
