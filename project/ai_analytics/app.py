import os
import sqlite3
import pandas as pd
from fastapi import FastAPI, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

app = FastAPI(title="AURA // Predictive Intelligence Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# PM2-safe directory resolution inside project/ai_analytics/
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(CURRENT_DIR, "frontend")
DATA_DIR = os.path.join(CURRENT_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "analytics.db")

# Exact path to your assets directory
ASSETS_DIR = r"C:\Users\marwa\OneDrive\Desktop\marwa_portfolio\assets"

def get_db():
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=500, detail=f"Database file not found at {DB_PATH}.")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

os.makedirs(FRONTEND_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# -------------------------------------------------------------
# STATIC FILE & ASSET MOUNTS
# -------------------------------------------------------------
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
    app.mount("/api/ai-analytics/static", StaticFiles(directory=FRONTEND_DIR), name="static_proxy")

# Mount your desktop assets folder directly
if os.path.exists(ASSETS_DIR):
    app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")
    app.mount("/api/ai-analytics/assets", StaticFiles(directory=ASSETS_DIR), name="assets_proxy")

# Explicit Favicon Route
@app.get("/favicon.ico")
@app.get("/assets/05-moon_98595.ico")
@app.get("/api/ai-analytics/assets/05-moon_98595.ico")
def serve_favicon():
    ico_path = os.path.join(ASSETS_DIR, "05-moon_98595.ico")
    if os.path.exists(ico_path):
        return FileResponse(ico_path, media_type="image/x-icon")
    raise HTTPException(status_code=404, detail="Favicon not found")

# Serve app.js directly if requested
@app.get("/app.js")
@app.get("/api/ai-analytics/app.js")
@app.get("/api/ai-analytics/static/app.js")
def serve_app_js():
    js_path = os.path.join(FRONTEND_DIR, "app.js")
    if not os.path.exists(js_path):
        js_path = os.path.join(CURRENT_DIR, "app.js")
    if os.path.exists(js_path):
        return FileResponse(js_path, media_type="application/javascript")
    raise HTTPException(status_code=404, detail="app.js not found")

@app.get("/")
@app.get("/api/ai-analytics")
@app.get("/api/ai-analytics/")
def read_root():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if not os.path.exists(index_path):
        index_path = os.path.join(CURRENT_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "AURA Engine Backend is active."}

@app.get("/api/kpis")
@app.get("/api/ai-analytics/api/kpis")
def get_kpis():
    conn = get_db()
    try:
        df = pd.read_sql("SELECT * FROM customer_predictions", conn)
    finally:
        conn.close()

    total_customers = int(len(df))
    if total_customers == 0:
        return {
            "total_customers": 0, 
            "avg_risk": 0, 
            "high_risk_count": 0, 
            "high_risk_pct": 0, 
            "revenue_at_risk": "$0"
        }

    avg_risk = float(df['risk_score'].mean())
    high_risk_count = int((df['risk_tier'] == 'High Risk').sum())
    est_revenue_at_risk = high_risk_count * 450

    return {
        "total_customers": total_customers,
        "avg_risk": round(avg_risk * 100, 1),
        "high_risk_count": high_risk_count,
        "high_risk_pct": round((high_risk_count / total_customers) * 100, 1),
        "revenue_at_risk": f"${est_revenue_at_risk:,}"
    }

@app.get("/api/charts/risk-distribution")
@app.get("/api/ai-analytics/api/charts/risk-distribution")
def get_risk_distribution():
    conn = get_db()
    try:
        df = pd.read_sql("SELECT risk_tier, COUNT(*) as count FROM customer_predictions GROUP BY risk_tier", conn)
    finally:
        conn.close()

    return {
        "labels": df['risk_tier'].tolist(),
        "data": df['count'].tolist()
    }

@app.get("/api/high-risk-customers")
@app.get("/api/ai-analytics/api/high-risk-customers")
def get_high_risk_customers():
    conn = get_db()
    try:
        df = pd.read_sql("""
            SELECT * FROM customer_predictions 
            WHERE risk_tier = 'High Risk' 
            ORDER BY risk_score DESC LIMIT 10
        """, conn)
    finally:
        conn.close()
    return df.to_dict(orient="records")

@app.post("/api/ai-query")
@app.post("/api/ai-analytics/api/ai-query")
def process_ai_query(data: dict = Body(...)):
    prompt = data.get("prompt", "").lower()
    conn = get_db()
    try:
        df = pd.read_sql("SELECT * FROM customer_predictions", conn)
    finally:
        conn.close()

    high_risk_count = (df['risk_tier'] == 'High Risk').sum()

    if "financial" in prompt or "revenue" in prompt or "cost" in prompt:
        insight = f"Financial Risk Exposure: <strong>${high_risk_count * 450:,}</strong> across {high_risk_count} flagged profiles."
    elif "driver" in prompt or "shap" in prompt or "why" in prompt:
        insight = "Key Churn Drivers (SHAP Analysis):<br>1. <strong>Low Recent Activity</strong><br>2. <strong>Month-to-Month Contract</strong><br>3. <strong>Support Escalations</strong>"
    else:
        insight = f"AURA Analysis: Currently evaluating <strong>{len(df):,}</strong> profiles with <strong>{high_risk_count}</strong> high-risk accounts."

    return {"insight": insight}

@app.post("/api/trigger-workflow")
@app.post("/api/ai-analytics/api/trigger-workflow")
def trigger_workflow():
    conn = get_db()
    try:
        count = pd.read_sql("SELECT COUNT(*) as c FROM customer_predictions WHERE risk_tier = 'High Risk'", conn).iloc[0]['c']
    finally:
        conn.close()
        
    return {
        "status": "success",
        "message": f"Autonomous Retention Campaign initialized for {count:,} flagged accounts."
    }

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5001)),
        reload=True
    )