const path = require('path'); // <--- Missing import added here

const PY = "C:\\Users\\marwa\\OneDrive\\Desktop\\marwa_portfolio\\.venv\\Scripts\\pythonw.exe";
const UVICORN = "C:\\Users\\marwa\\OneDrive\\Desktop\\marwa_portfolio\\.venv\\Scripts\\uvicorn.exe";
const ROOT = "C:\\Users\\marwa\\OneDrive\\Desktop\\marwa_portfolio";

module.exports = {
  apps: [
    // --- 1. MAIN PORTFOLIO ROOT (Flask) ---
    {
      name: "main-portfolio",
      script: `${ROOT}\\server.py`,
      cwd: ROOT,
      interpreter: PY,
      autorestart: true,
      max_restarts: 5,
      windowsHide: true,
      env: { PORT: "5000", PYTHONPATH: ROOT }
    },

    // --- 2. FASTAPI BACKEND SERVICES ---
    {
      name: "ai-analytics-backend",
      script: UVICORN,
      args: "app:app --host 0.0.0.0 --port 5001",
      cwd: `${ROOT}\\project\\ai_analytics`,
      interpreter: "none",
      autorestart: true,
      max_restarts: 5,
      windowsHide: true
    },
    {
      name: "autoinsight-backend",
      script: UVICORN,
      args: "main:app --host 0.0.0.0 --port 5003",
      cwd: `${ROOT}\\project\\automated_ai`,
      interpreter: "none",
      autorestart: true,
      max_restarts: 5,
      windowsHide: true
    },
    {
      name: "queitspace-backend",
      script: UVICORN,
      args: "QS:app --host 0.0.0.0 --port 5006",
      cwd: `${ROOT}\\project\\queitspace`,
      interpreter: "none",
      autorestart: true,
      max_restarts: 5,
      windowsHide: true
    },

    // --- 3. FLASK BACKEND SERVICES ---
    {
      name: "aifa-backend",
      script: `${ROOT}\\project\\AIFA\\aifa.py`,
      cwd: `${ROOT}\\project\\AIFA`,
      interpreter: PY,
      autorestart: true,
      max_restarts: 5,
      windowsHide: true,
      env: { PORT: "5002", PYTHONPATH: `${ROOT}\\project\\AIFA` }
    },
    {
      name: "devhub-backend",
      script: `${ROOT}\\project\\devhub_project\\devhub.py`,
      cwd: `${ROOT}\\project\\devhub_project`,
      interpreter: PY,
      autorestart: true,
      max_restarts: 5,
      windowsHide: true,
      env: { PORT: "5004", PYTHONPATH: `${ROOT}\\project\\devhub_project` }
    },
    {
      name: "movie-backend",
      script: `${ROOT}\\project\\movie\\movie.py`,
      cwd: `${ROOT}\\project\\movie`,
      interpreter: PY,
      autorestart: true,
      max_restarts: 5,
      windowsHide: true,
      env: { PORT: "5005", PYTHONPATH: `${ROOT}\\project\\movie` }
    },
    {
      name: "stock-dashboard-backend",
      script: `${ROOT}\\project\\stock_dashboard\\stock.py`,
      cwd: `${ROOT}\\project\\stock_dashboard`,
      interpreter: PY,
      autorestart: true,
      max_restarts: 5,
      windowsHide: true,
      env: { PORT: "5007", PYTHONPATH: `${ROOT}\\project\\stock_dashboard` }
    },

    // --- 4. FRONTEND SERVERS ---
    {
      name: "autoinsight-frontend",
      script: `${ROOT}\\project\\automated_ai\\frontend\\node_modules\\vite\\bin\\vite.js`,
      args: "--host 127.0.0.1 --port 5008",
      cwd: `${ROOT}\\project\\automated_ai\\frontend`,
      autorestart: true,
      max_restarts: 5,
      windowsHide: true,
      env: { PORT: "5008", NODE_ENV: "development", VITE_API_BASE: "/api/autoinsight" }
    }
  ]
};