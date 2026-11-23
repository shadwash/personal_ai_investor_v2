# Personal AI Investor 2.0

A free-data Streamlit research application. It discovers a rotating set of market candidates, evaluates business quality and technical structure independently, estimates valuation scenarios when possible, and creates an investment research report with entry and risk levels.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud

1. Create a GitHub repository (or a new branch/repository for v2).
2. Upload the complete contents of this folder, preserving the directory structure.
3. In Streamlit Community Cloud, deploy `app.py` from the repository root.
4. No API keys or paid services are required.

## Research design

- Market discovery: Yahoo Finance screeners plus a rotating sample of Nasdaq Trader symbol directories.
- Business Quality: reported growth, margins, ROE, free cash flow, leverage and valuation fields when available.
- Technical Intelligence: trend, momentum, RSI, relative volume and price structure.
- Valuation: transparent forward-EPS / forward-P/E sensitivity model; not DCF or analyst consensus.
- Shield: flags data gaps and potential risk conditions.
- Opportunity Rank: starting weights 35% business quality, 35% technical strength, 20% valuation attractiveness and 10% catalyst context. Missing components are renormalized, with coverage shown separately.

## Important limitations

Yahoo Finance data can be delayed, incomplete, rate-limited or unavailable. The candidate pool is sampled and is not an exhaustive scan of every listed security. Streamlit Cloud's local filesystem is not durable storage; research history may reset on restart or redeploy. This application is informational only and does not connect to a brokerage or execute trades.
