const path = require('path');

// Dynamically check if running inside Docker container or local Windows environment
const IS_DOCKER = process.env.RAILWAY_ENVIRONMENT || process.env.DOCKER_CONTAINER || !process.platform.startsWith('win');

const ROOT = IS_DOCKER ? '/app' : "C:\\Users\\marwa\\OneDrive\\Desktop\\marwa_portfolio";
const PY = IS_DOCKER ? 'python3' : `${ROOT}\\.venv\\Scripts\\pythonw.exe`;
const UVICORN = IS_DOCKER ? 'uvicorn' : `${ROOT}\\.venv\\Scripts\\uvicorn.exe`;
const VITE_BIN = IS_DOCKER ? './node_modules/vite/bin/vite.js' : `${ROOT}\\project\\automated_ai\\frontend\\node_modules\\vite\\bin\\vite.js`;

module.exports = {
  apps: [
    // --- 1. MAIN PORTFOLIO ROOT (Flask) ---
    {
      name: "main-portfolio",
      script: path.join(ROOT, 'server.py'),
      cwd: ROOT,
      interpreter: IS_DOCKER ? 'python3' : PY,
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
      cwd: path.join(ROOT, 'project', 'ai_analytics'),
      interpreter: "none",
      autorestart: true,
      max_restarts: 5,
      windowsHide: true
    },
    {
      name: "autoinsight-backend",
      script: UVICORN,
      args: "main:app --host 0.0.0.0 --port 5003",
      cwd: path.join(ROOT, 'project', 'automated_ai'),
      interpreter: "none",
      autorestart: true,
      max_restarts: 5,
      windowsHide: true
    },
    {
      name: "queitspace-backend",
      script: UVICORN,
      args: "QS:app --host 0.0.0.0 --port 5006",
      cwd: path.join(ROOT, 'project', 'queitspace'),
      interpreter: "none",
      autorestart: true,
      max_restarts: 5,
      windowsHide: true
    },

    // --- 3. FLASK BACKEND SERVICES ---
    {
      name: "aifa-backend",
      script: path.join(ROOT, 'project', 'AIFA', 'aifa.py'),
      cwd: path.join(ROOT, 'project', 'AIFA'),
      interpreter: IS_DOCKER ? 'python3' : PY,
      autorestart: true,
      max_restarts: 5,
      windowsHide: true,
      env: { PORT: "5002", PYTHONPATH: path.join(ROOT, 'project', 'AIFA') }
    },
    {
      name: "devhub-backend",
      script: path.join(ROOT, 'project', 'devhub_project', 'devhub.py'),
      cwd: path.join(ROOT, 'project', 'devhub_project'),
      interpreter: IS_DOCKER ? 'python3' : PY,
      autorestart: true,
      max_restarts: 5,
      windowsHide: true,
      env: { PORT: "5004", PYTHONPATH: path.join(ROOT, 'project', 'devhub_project') }
    },
    {
      name: "movie-backend",
      script: path.join(ROOT, 'project', 'movie', 'movie.py'),
      cwd: path.join(ROOT, 'project', 'movie'),
      interpreter: IS_DOCKER ? 'python3' : PY,
      autorestart: true,
      max_restarts: 5,
      windowsHide: true,
      env: { PORT: "5005", PYTHONPATH: path.join(ROOT, 'project', 'movie') }
    },
    {
      name: "stock-dashboard-backend",
      script: path.join(ROOT, 'project', 'stock_dashboard', 'stock.py'),
      cwd: path.join(ROOT, 'project', 'stock_dashboard'),
      interpreter: IS_DOCKER ? 'python3' : PY,
      autorestart: true,
      max_restarts: 5,
      windowsHide: true,
      env: { PORT: "5007", PYTHONPATH: path.join(ROOT, 'project', 'stock_dashboard') }
    },

    // --- 4. FRONTEND SERVERS ---
    {
      name: "autoinsight-frontend",
      script: VITE_BIN,
      args: "--host 0.0.0.0 --port 5008",
      cwd: path.join(ROOT, 'project', 'automated_ai', 'frontend'),
      autorestart: true,
      max_restarts: 5,
      windowsHide: true,
      env: { PORT: "5008", NODE_ENV: "development", VITE_API_BASE: "/api/autoinsight" }
    }
  ]
};