import io
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid

from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import numpy as np
import pandas as pd
from pydantic import BaseModel
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split

from modules.visualizer import generate_visualizations, _sanitize_dict, _sanitize_val

# ==========================================
# Application Setup & Environment Setup
# ==========================================

app = FastAPI(title="AutoInsight AI Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PROCESSED_DIR = Path("processed_data").resolve()
UPLOAD_DIR = Path("upload_data").resolve()

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Temporary session store and trained models store
SESSION_STORE: Dict[str, Dict[str, Any]] = {}
MODEL_STORE: Dict[str, Dict[str, Any]] = {}


# ==========================================
# 1. JSON Safety & Security Helpers
# ==========================================

def _is_strict_identifier(col_name: str) -> bool:
    """Detects system ID columns that shouldn't be visualized."""
    if not col_name:
        return False
    lower = str(col_name).lower().strip()
    return lower in ['id', 'index', 'uuid', 'unnamed: 0'] or lower.endswith('_id')


def resolve_safe_path(base_dir: Path, filename: str) -> Path:
    """Ensures file strictly resides inside target directory (Path Traversal Protection)."""
    safe_filename = Path(filename).name
    file_path = (base_dir / safe_filename).resolve()

    if not file_path.is_relative_to(base_dir):
        raise HTTPException(status_code=400, detail="Invalid file path.")

    return file_path


def load_dataset(file_path: Path) -> pd.DataFrame:
    """Loads a DataFrame safely from CSV or Excel formats."""
    suffix = file_path.suffix.lower()
    if suffix == '.csv':
        return pd.read_csv(file_path)
    elif suffix in ['.xls', '.xlsx']:
        return pd.read_excel(file_path)
    else:
        raise HTTPException(status_code=400, detail="Unsupported file format.")


def _get_session_data(session_id: str, source: str = "processed") -> pd.DataFrame:
    if session_id not in SESSION_STORE:
        raise HTTPException(status_code=404, detail="Session expired or dataset not found.")
    
    df = SESSION_STORE[session_id]["processed_df"] if source == "processed" else SESSION_STORE[session_id]["raw_df"]
    if df is None:
        raise HTTPException(status_code=404, detail="No active dataset found for this session.")
    return df


# ==========================================
# 2. Pydantic Models
# ==========================================

class CleanRequest(BaseModel):
    filename: Optional[str] = None
    remove_dup: bool = False


class CustomizeVisualsRequest(BaseModel):
    included_columns: Optional[List[str]] = None
    max_rows: Optional[int] = None


# ==========================================
# 3. API Endpoints
# ==========================================

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        session_id = str(uuid.uuid4())
        contents = await file.read()
        
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        elif file.filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format.")
            
        SESSION_STORE[session_id] = {
            "raw_df": df.copy(),
            "processed_df": df.copy(),
            "filename": file.filename
        }

        # Save to disk for filesystem path endpoints
        df.to_csv(UPLOAD_DIR / file.filename, index=False)
        df.to_csv(PROCESSED_DIR / f"cleaned_{file.filename}", index=False)

        # Generate default visualizations on initial file upload
        default_visuals = generate_visualizations(df)

        metadata = {
            "session_id": session_id,
            "filename": file.filename,
            "num_rows": len(df),
            "num_cols": len(df.columns),
            "columns": list(df.columns),
            "data_types": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "duplicate_rows": int(df.duplicated().sum())
        }
        return {
            "status": "success", 
            "session_id": session_id,
            "metadata": metadata,
            "visualizations": default_visuals
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/visualize")
async def visualize_data(
    x_session_id: str = Header(..., alias="X-Session-ID"), 
    source: str = "processed"
):
    df = _get_session_data(x_session_id, source)
    return generate_visualizations(df)


@app.post("/visualize/customize")
async def customize_visualizations(
    req: CustomizeVisualsRequest,
    x_session_id: str = Header(..., alias="X-Session-ID")
):
    df = _get_session_data(x_session_id, "processed")
    target_df = df.copy()

    if req.max_rows and req.max_rows > 0:
        target_df = target_df.head(req.max_rows)

    visuals = generate_visualizations(target_df, included_columns=req.included_columns)
    return {"status": "success", "visualizations": visuals}


@app.get("/preview")
async def preview_data(
    x_session_id: str = Header(..., alias="X-Session-ID"), 
    source: str = "processed"
):
    df = _get_session_data(x_session_id, source)
    sample = df.head(100).fillna("").to_dict(orient="records")
    return {"rows": sample}


@app.get("/preview/{filename}")
async def preview_data_by_filename(filename: str, source: str = "processed"):
    base_dir = PROCESSED_DIR if source == "processed" else UPLOAD_DIR
    target_name = f"cleaned_{filename}" if source == "processed" else filename
    file_path = resolve_safe_path(base_dir, target_name)
    
    if not file_path.exists():
        file_path = resolve_safe_path(UPLOAD_DIR, filename)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found.")

    df = load_dataset(file_path)
    sample = df.head(100).fillna("").to_dict(orient="records")
    return {"rows": sample}


@app.post("/clean")
async def clean_data(
    req: CleanRequest, 
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    # Lookup by session_id or fallback to last session
    if not x_session_id or x_session_id not in SESSION_STORE:
        if SESSION_STORE:
            x_session_id = list(SESSION_STORE.keys())[-1]
        else:
            raise HTTPException(status_code=404, detail="No active session found.")

    df = _get_session_data(x_session_id, "processed")
    logs = []
    
    if req.remove_dup:
        initial_count = len(df)
        df = df.drop_duplicates()
        removed = initial_count - len(df)
        logs.append(f"Removed {removed} duplicate rows.")

    SESSION_STORE[x_session_id]["processed_df"] = df

    # Sync processed file on disk
    filename = SESSION_STORE[x_session_id].get("filename", "dataset.csv")
    df.to_csv(PROCESSED_DIR / f"cleaned_{filename}", index=False)

    metadata = {
        "num_rows": len(df),
        "num_cols": len(df.columns),
        "columns": list(df.columns),
        "data_types": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "duplicate_rows": int(df.duplicated().sum())
    }
    
    updated_visuals = generate_visualizations(df)

    return {
        "status": "success", 
        "logs": logs, 
        "metadata": metadata, 
        "metadata_after": metadata,
        "visualizations": updated_visuals
    }


@app.get("/export")
async def export_cleaned_data(x_session_id: Optional[str] = Header(None, alias="X-Session-ID")):
    if not x_session_id or x_session_id not in SESSION_STORE:
        if SESSION_STORE:
            x_session_id = list(SESSION_STORE.keys())[-1]
        else:
            raise HTTPException(status_code=404, detail="No processed data available to export.")

    df = SESSION_STORE[x_session_id]["processed_df"]
    stream = io.StringIO()
    df.to_csv(stream, index=False)
    stream.seek(0)

    filename = SESSION_STORE[x_session_id].get("filename", "cleaned_data.csv")
    
    return StreamingResponse(
        io.BytesIO(stream.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=cleaned_{filename}"}
    )


@app.post("/train")
async def train_model(
    filename: str, 
    target_column: str, 
    model_name: str = "ui_model", 
    source: str = "processed",
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    if x_session_id and x_session_id in SESSION_STORE:
        df = SESSION_STORE[x_session_id]["processed_df"]
    else:
        base_dir = PROCESSED_DIR if source == "processed" else UPLOAD_DIR
        target_name = f"cleaned_{filename}" if source == "processed" else filename
        file_path = resolve_safe_path(base_dir, target_name)
        if not file_path.exists():
            file_path = resolve_safe_path(UPLOAD_DIR, filename)
        df = load_dataset(file_path)

    if target_column not in df.columns:
        raise HTTPException(status_code=400, detail=f"Target column '{target_column}' not found.")

    clean_df = df.dropna(subset=[target_column]).copy()
    X = clean_df.drop(columns=[target_column])
    y = clean_df[target_column]

    # Keep non-identifier features
    feature_cols = [c for c in X.columns if not _is_strict_identifier(c)]
    X = X[feature_cols]

    # Simple numeric encoding for categorical columns
    for col in X.select_dtypes(include=['object', 'category']).columns:
        X[col] = X[col].astype('category').cat.codes

    is_classification = y.dtype == 'object' or y.nunique() <= 10
    if is_classification:
        y_encoded = y.astype('category').cat.codes if y.dtype == 'object' else y
        model = RandomForestClassifier(n_estimators=50, random_state=42)
        X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42)
        model.fit(X_train, y_train)
        score = model.score(X_test, y_test)
        metric_name = "Accuracy Score"
    else:
        model = RandomForestRegressor(n_estimators=50, random_state=42)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        model.fit(X_train, y_train)
        score = model.score(X_test, y_test)
        metric_name = "R² Score"

    importances = model.feature_importances_
    feature_importance_list = [
        {"feature": str(col), "importance": float(imp)}
        for col, imp in zip(X.columns, importances)
    ]
    feature_importance_list.sort(key=lambda x: x["importance"], reverse=True)

    MODEL_STORE[model_name] = {
        "model": model,
        "feature_cols": list(X.columns),
        "is_classification": is_classification,
        "target_col": target_column
    }

    return {
        "status": "success",
        "model_results": {
            "metrics": {
                "metric_name": metric_name,
                "metric_value": round(float(score), 4)
            },
            "feature_importances": feature_importance_list
        }
    }


@app.post("/predict/{model_name}")
async def predict(model_name: str, payload: Dict[str, Any]):
    if model_name not in MODEL_STORE:
        raise HTTPException(status_code=404, detail="Requested model does not exist or has not been trained.")

    model_info = MODEL_STORE[model_name]
    model = model_info["model"]
    feature_cols = model_info["feature_cols"]

    input_data = []
    for col in feature_cols:
        val = payload.get(col, 0)
        try:
            val = float(val)
        except (ValueError, TypeError):
            val = 0.0
        input_data.append(val)

    prediction = model.predict([input_data])[0]
    return {"status": "success", "prediction": _sanitize_val(prediction)}


@app.get("/api/visualize/{filename}")
def get_visualizations_by_path(filename: str, source: str = "processed"):
    base_dir = PROCESSED_DIR if source == "processed" else UPLOAD_DIR
    target_name = f"cleaned_{filename}" if source == "processed" else filename

    file_path = resolve_safe_path(base_dir, target_name)

    if not file_path.exists():
        if source == "processed":
            file_path = resolve_safe_path(UPLOAD_DIR, filename)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Requested file not found in system.")

    try:
        df = load_dataset(file_path)
        visual_data = generate_visualizations(df)
        return {
            "status": "success",
            "filename": filename,
            "visualizations": visual_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Visualization failed: {str(e)}")

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )