<div align="center">

# `marwa.portfolio`

**Architectural Suite & Multi-Service Web System**

[Portfolio Live](https://marwaabubaker.is-a.dev) • [GitHub](https://github.com/5marvv)

---

</div>

### Overview

A unified portfolio architecture hosting standalone backend engines, data pipelines, and interactive web tools. Controlled through a single Flask proxy entrypoint (`server.py`) and orchestrated continuously across background services.


---

### Featured Projects

#### 01. AutoInsight AI
> *Automated dataset parsing, validation, and rapid model evaluation designed to eliminate routine data cleaning friction.*
* **Stack:** React (Vite), FastAPI, Python, Tailwind CSS
* **Route:** `/api/autoinsight-frontend/`

#### 02. DevHub AI Companion
> *Customizable developer companion interface powered by OpenRouter API streaming routes.*
* **Stack:** Flask, OpenRouter API, JavaScript
* **Route:** `/api/devhub/`

#### 03. Visual Dispatch
> *Interactive metrics dashboard synthesizing financial, customer service, and order metrics into unified visual views.*
* **Stack:** Python, Excel Integration, Web Canvas

---

### Architecture & Service Registry

```text
PORT     SERVICE TYPE             TECH STACK
5000     Main Portfolio Proxy     Flask / Python
5001     Analytics Service        FastAPI / Uvicorn
5002     AIFA Engine              Flask
5003     AutoInsight Backend      FastAPI / Uvicorn
5004     DevHub Backend           Flask
5005     Media / Movie API        Flask
5006     QuietSpace Engine        FastAPI / Uvicorn
5007     Stock Dashboard          Flask
5008     AutoInsight Frontend     Vite / React
```

## Local Development

### Clone the repository:

```Bash
git clone [https://github.com/5marvv/marwa-portfolio.git](https://github.com/5marvv/marwa-portfolio.git)
cd marwa-portfolio
```

### Set up Python virtual environment:

```Bash
python -m venv .venv
source .venv/Scripts/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Start complete process tree (PM2):

```Bash
pm2 start ecosystem.config.js
```

### Designed & Maintained by Marwa Abubaker (@5marvv)