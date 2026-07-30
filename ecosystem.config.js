const path = require("path");

const ROOT = __dirname;
const IS_WINDOWS = process.platform === "win32";

const PY = IS_WINDOWS ? "python" : "python3";
const UVICORN = "uvicorn";

module.exports = {
  apps: [
    // --- 1. MAIN PORTFOLIO ROOT (Flask) ---
    {
      name: "main-portfolio",
      script: "server.py",
      cwd: ROOT,
      interpreter: PY,
      autorestart: true,
      max_restarts: 5,
      env: { PORT: process.env.PORT || "5000", PYTHONPATH: ROOT }
    },

    // --- 2. FASTAPI BACKEND SERVICES ---
    {
      name: "ai-analytics-backend",
      script: UVICORN,
      args: "app:app --host 0.0.0.0 --port 5001",
      cwd: path.join(ROOT, "project", "ai_analytics"),
      interpreter: "none",
      autorestart: true,
      max_restarts: 5
    },
    {
      name: "autoinsight-backend",
      script: UVICORN,
      args: "main:app --host 0.0.0.0 --port 5003",
      cwd: path.join(ROOT, "project", "automated_ai"),
      interpreter: "none",
      autorestart: true,
      max_restarts: 5
    },
    {
      name: "queitspace-backend",
      script: UVICORN,
      args: "QS:app --host 0.0.0.0 --port 5006",
      cwd: path.join(ROOT, "project", "queitspace"),
      interpreter: "none",
      autorestart: true,
      max_restarts: 5
    },

    // --- 3. FLASK BACKEND SERVICES ---
    {
      name: "aifa-backend",
      script: "aifa.py",
      cwd: path.join(ROOT, "project", "AIFA"),
      interpreter: PY,
      autorestart: true,
      max_restarts: 5,
      env: { PORT: "5002", PYTHONPATH: path.join(ROOT, "project", "AIFA") }
    },
    {
      name: "devhub-backend",
      script: "devhub.py",
      cwd: path.join(ROOT, "project", "devhub_project"),
      interpreter: PY,
      autorestart: true,
      max_restarts: 5,
      env: { PORT: "5004", PYTHONPATH: path.join(ROOT, "project", "devhub_project") }
    },
    {
      name: "movie-backend",
      script: "movie.py",
      cwd: path.join(ROOT, "project", "movie"),
      interpreter: PY,
      autorestart: true,
      max_restarts: 5,
      env: { PORT: "5005", PYTHONPATH: path.join(ROOT, "project", "movie") }
    },
    {
      name: "stock-dashboard-backend",
      script: "stock.py",
      cwd: path.join(ROOT, "project", "stock_dashboard"),
      interpreter: PY,
      autorestart: true,
      max_restarts: 5,
      env: { PORT: "5007", PYTHONPATH: path.join(ROOT, "project", "stock_dashboard") }
    }
  ]
};