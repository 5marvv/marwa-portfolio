# modules/loader.py
import pandas as pd
import os
from typing import Dict, Any

def load_dataset(file_path: str) -> pd.DataFrame:
    """
    Loads a CSV or Excel file safely into a Pandas DataFrame.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file at {file_path} does not exist.")
        
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.csv':
        return pd.read_csv(file_path)
    elif ext in ['.xls', '.xlsx']:
        return pd.read_excel(file_path)
    else:
        raise ValueError("Unsupported file format. Please upload a CSV or Excel file.")

def get_basic_meta(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generates structural metadata and diagnostics from the DataFrame.
    """
    # Calculate missing values per column
    missing_counts = df.isnull().sum().to_dict()
    missing_percentages = (df.isnull().mean() * 100).round(2).to_dict()
    
    # Bundle columns with their data types and missing stats
    column_details = []
    for col in df.columns:
        column_details.append({
            "name": col,
            "type": str(df[col].dtype),
            "missing_count": int(missing_counts[col]),
            "missing_percentage": float(missing_percentages[col])
        })

    return {
        "total_rows": len(df),
        "num_rows": len(df),
        "row_count": len(df),
        "total_cols": len(df.columns),
        "num_cols": len(df.columns),
        "duplicate_rows": int(df.duplicated().sum()),
        "columns": list(df.columns),
        "data_types": {col: str(dtype) for col, dtype in df.dtypes.items()}
    }