# AURA

> Predictive Analytics & Risk Management Engine

AURA is a full-stack predictive intelligence platform designed to monitor customer churn probability, evaluate financial risk exposure, and trigger automated retention workflows through a modern analytical interface.

---

## Key Features

* **Real-time KPI Tracking**: Instant visibility into total monitored accounts, mean churn probability, high-risk cohorts, and total revenue exposure.
* **Risk Distribution Analytics**: Categorized churn risk segmentation powered by machine learning outputs and visualized with Chart.js.
* **Conversational AI Copilot**: Natural language query engine capable of interpreting dataset trends, identifying key churn drivers, and projecting financial impact.
* **Priority Queue Management**: Structured list of top high-risk accounts requiring immediate intervention.
* **Theme Support**: Seamless switching between light and dark visual interfaces.

---

## System Architecture

### Tech Stack

* **Frontend**: HTML5, Tailwind CSS, JavaScript (ES6+), Chart.js
* **Backend**: Python 3.10+, FastAPI, Uvicorn
* **Data Layer**: SQLite3, Pandas

### Project Structure

```text
.
├── app.py                  # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── data/
│   └── analytics.db        # SQLite analytical database
├── frontend/
│   ├── index.html          # Dashboard user interface
│   └── app.js              # Client-side state and API handling
└── src/
    └── server.py           # Optional modular server structure
```

## Getting Started

### Prerequisites
* Python 3.9 or higher
* `pip` package manager

### Installation

1. Clone the repository:
   ```bash
   git clone [https://github.com/your-organization/lumen.git](https://github.com/your-organization/lumen.git)
   cd lumen

### Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

### Install required dependencies:

```bash
pip install -r requirements.txt
```

## Usage
Start the development server using Uvicorn:

```Bash
python -m uvicorn app:app --reload
```

Once running, access the dashboard at:

http://127.0.0.1:8000


## API Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/` | `GET` | Serves the main application dashboard. |
| `/api/kpis` | `GET` | Returns high-level metrics (total accounts, risk averages, revenue exposure). |
| `/api/charts/risk-distribution` | `GET` | Returns aggregated risk segmentation data for chart rendering. |
| `/api/high-risk-customers` | `GET` | Fetches the top 10 accounts categorized as high risk. |
| `/api/ai-query` | `POST` | Processes natural language queries and returns analytical insights. |
| `/api/trigger-workflow` | `POST` | Initiates the automated retention sequence for flagged profiles. |

---

## License

Distributed under the MIT License. See `LICENSE` for more information.