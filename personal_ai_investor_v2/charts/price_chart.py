import numpy as np
import plotly.graph_objects as go

def build_chart(data, show_entries=True, show_valuation=False):
    h=data["history"].tail(260).copy(); t=data["technical"]; e=data["entries"]; v=data["valuation"]
    fig=go.Figure()
    fig.add_trace(go.Candlestick(x=h.index,open=h.Open,high=h.High,low=h.Low,close=h.Close,name="Price"))
    for key,label,color in [("ma20","20-day MA","#2b8a66"),("ma50","50-day MA","#d18b35"),("ma200","200-day MA","#777d85")]:
        if np.isfinite(t.get(key,np.nan)):
            period=int(key[2:]); series=h.Close.rolling(period).mean()
            fig.add_trace(go.Scatter(x=h.index,y=series,name=label,line=dict(width=1.5,color=color)))
    if show_entries:
        for key,label,color,dash in [("early_low","Early entry low","#25845c","dot"),("early_high","Early entry high","#25845c","dot"),("breakout","Breakout confirmation","#3977b8","dash"),("invalidation","Invalidation","#c14d4d","dash")]:
            y=e.get(key,np.nan)
            if np.isfinite(y): fig.add_hline(y=y,line_dash=dash,line_color=color,annotation_text=f"{label} ${y:.2f}",annotation_position="top left")
    if show_valuation:
        for key,label,color in [("bear","Bear value","#bd6666"),("base","Base value","#777d85"),("bull","Bull value","#398765")]:
            y=v.get(key,np.nan)
            if np.isfinite(y): fig.add_hline(y=y,line_dash="dot",line_color=color,annotation_text=f"{label} ${y:.2f}",annotation_position="bottom right")
    fig.update_layout(height=560,template="plotly_white",margin=dict(l=10,r=20,t=30,b=10),xaxis_rangeslider_visible=False,legend=dict(orientation="h",y=1.02),hovermode="x unified")
    return fig
