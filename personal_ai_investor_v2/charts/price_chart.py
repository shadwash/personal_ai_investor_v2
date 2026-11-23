import numpy as np
import plotly.graph_objects as go

def build_chart(data, show_entries=True, show_valuation=False):
    h=data["history"].tail(260).copy(); t=data["technical"]; e=data["entries"]; v=data["valuation"]
    fig=go.Figure()
    fig.add_trace(go.Candlestick(x=h.index,open=h.Open,high=h.High,low=h.Low,close=h.Close,name="Price",increasing_line_color="#22c55e",decreasing_line_color="#fb7185",increasing_fillcolor="#22c55e",decreasing_fillcolor="#fb7185"))
    for key,label,color in [("ma20","20-day MA","#2dd4bf"),("ma50","50-day MA","#fbbf24"),("ma200","200-day MA","#a5b4fc")]:
        if np.isfinite(t.get(key,np.nan)):
            period=int(key[2:]); series=h.Close.rolling(period).mean()
            fig.add_trace(go.Scatter(x=h.index,y=series,name=label,line=dict(width=1.5,color=color)))
    if show_entries:
        for key,label,color,dash in [("early_low","Early entry low","#4ade80","dot"),("early_high","Early entry high","#4ade80","dot"),("breakout","Breakout confirmation","#38bdf8","dash"),("invalidation","Invalidation","#fb7185","dash")]:
            y=e.get(key,np.nan)
            if np.isfinite(y): fig.add_hline(y=y,line_dash=dash,line_color=color,annotation_text=f"{label} ${y:.2f}",annotation_position="top left")
    if show_valuation:
        for key,label,color in [("bear","Bear value","#fb7185"),("base","Base value","#cbd5e1"),("bull","Bull value","#4ade80")]:
            y=v.get(key,np.nan)
            if np.isfinite(y): fig.add_hline(y=y,line_dash="dot",line_color=color,annotation_text=f"{label} ${y:.2f}",annotation_position="bottom right")
    fig.update_layout(height=560,template="plotly_dark",paper_bgcolor="#0d192b",plot_bgcolor="#0d192b",font=dict(color="#dce8f5",family="Arial"),margin=dict(l=10,r=20,t=38,b=10),xaxis_rangeslider_visible=False,legend=dict(orientation="h",y=1.04,font=dict(color="#cbd5e1")),hovermode="x unified")
    fig.update_xaxes(showgrid=True,gridcolor="#24364d",linecolor="#405570",zerolinecolor="#24364d")
    fig.update_yaxes(showgrid=True,gridcolor="#24364d",linecolor="#405570",zerolinecolor="#24364d")
    return fig
