# modules/visualizer.py
from typing import Any, Dict, List, Optional
import pandas as pd
import numpy as np

# --- JSON Safety & Serialization Helpers ---

def _sanitize_val(val: Any) -> Any:
    """Recursively replaces NaN, Inf, and NumPy types with JSON-compliant native Python types."""
    if isinstance(val, (float, np.floating)):
        if np.isnan(val) or np.isinf(val):
            return None
        return float(val)
    if isinstance(val, (int, np.integer)):
        return int(val)
    if isinstance(val, (bool, np.bool_)):
        return bool(val)
    if pd.isna(val):
        return None
    return str(val) if not isinstance(val, (str, list, dict)) else val


def _sanitize_dict(data: dict) -> dict:
    """Sanitizes entire dictionary structures for JSON safety."""
    clean = {}
    for k, v in data.items():
        if isinstance(v, dict):
            clean[str(k)] = _sanitize_dict(v)
        elif isinstance(v, list):
            clean[str(k)] = [_sanitize_dict(i) if isinstance(i, dict) else _sanitize_val(i) for i in v]
        else:
            clean[str(k)] = _sanitize_val(v)
    return clean


def _is_strict_identifier(col_name: str) -> bool:
    if not col_name:
        return False
    lower = str(col_name).lower().strip()
    return lower in ['id', 'index', 'uuid', 'unnamed: 0'] or lower.endswith('_id')


# --- Main Visualization Engine ---

def generate_visualizations(
    df: pd.DataFrame, 
    max_cols: int = 10, 
    included_columns: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Parses a DataFrame and returns structured JSON chart configurations 
    ready for frontend rendering engines. Support custom column inclusions.
    """
    if df.empty:
        return {
            "charts": [],
            "correlation_matrix": {},
            "missing_data_chart": [],
            "summary": {"total_charts": 0, "message": "Dataset is empty."}
        }

    # Filter DataFrame to include only requested columns
    if included_columns:
        valid_cols = [c for c in included_columns if c in df.columns]
        df_target = df[valid_cols] if valid_cols else df.copy()
    else:
        df_target = df.copy()

    charts: List[Dict[str, Any]] = []

    # 1. Column Type Inference
    numeric_cols = [c for c in df_target.select_dtypes(include=[np.number]).columns if not _is_strict_identifier(c)]
    categorical_cols = [c for c in df_target.select_dtypes(include=['object', 'category', 'bool']).columns if not _is_strict_identifier(c)]
    
    # Identify datetime columns
    datetime_cols = []
    for col in df_target.columns:
        if col not in numeric_cols and pd.api.types.is_datetime64_any_dtype(df_target[col]):
            datetime_cols.append(col)
        elif col not in numeric_cols and col not in categorical_cols:
            try:
                sample = df_target[col].dropna().head(10)
                if not sample.empty and pd.to_datetime(sample, errors='coerce').notna().all():
                    datetime_cols.append(col)
            except Exception:
                pass

    # --- CHART GENERATOR 1: Missing Data Overview ---
    missing_series = df_target.isnull().sum()
    missing_data = []
    for col, count in missing_series.items():
        if count > 0:
            missing_data.append({
                "column": str(col),
                "missing_count": int(count),
                "missing_percentage": round(float((count / len(df_target)) * 100), 2)
            })
    
    if missing_data:
        charts.append({
            "id": "missing_data_overview",
            "title": "Missing Values by Column",
            "type": "bar",
            "x_axis": "column",
            "y_axis": "missing_percentage",
            "description": "Percentage of missing records across variables",
            "data": missing_data
        })

    # --- CHART GENERATOR 2: Numerical Histograms & Box Plots ---
    for col in numeric_cols[:max_cols]:
        clean_series = df_target[col].dropna()
        if clean_series.empty or clean_series.nunique() <= 1:
            continue

        # A. Histogram / Binned Distribution
        counts, bin_edges = np.histogram(clean_series, bins=min(12, int(clean_series.nunique())))
        bins_data = [
            {
                "range": f"{round(float(bin_edges[i]), 2)} - {round(float(bin_edges[i+1]), 2)}",
                "count": int(counts[i])
            }
            for i in range(len(counts))
        ]
        charts.append({
            "id": f"hist_{col}",
            "title": f"Distribution of {col}",
            "type": "histogram",
            "x_axis": "range",
            "y_axis": "count",
            "data": bins_data
        })

        # B. Outlier & Quartile Box Plot Metrics
        q1 = float(clean_series.quantile(0.25))
        median = float(clean_series.median())
        q3 = float(clean_series.quantile(0.75))
        iqr = q3 - q1
        lower_bound = q1 - (1.5 * iqr)
        upper_bound = q3 + (1.5 * iqr)
        
        outliers_count = int(((clean_series < lower_bound) | (clean_series > upper_bound)).sum())

        charts.append({
            "id": f"boxplot_{col}",
            "title": f"{col} Summary (Box Plot Specs)",
            "type": "boxplot",
            "data": [{
                "min": _sanitize_val(clean_series.min()),
                "q1": round(q1, 2),
                "median": round(median, 2),
                "q3": round(q3, 2),
                "max": _sanitize_val(clean_series.max()),
                "outliers_count": outliers_count
            }]
        })

    # --- CHART GENERATOR 3: Categorical Value Distribution ---
    for col in categorical_cols[:max_cols]:
        clean_series = df_target[col].dropna().astype(str)
        if clean_series.empty:
            continue

        value_counts = clean_series.value_counts()
        
        top_cats = value_counts.head(7)
        if len(value_counts) > 7:
            other_sum = value_counts.iloc[7:].sum()
            bar_data = [{"category": str(k), "count": int(v)} for k, v in top_cats.items()]
            bar_data.append({"category": "Other", "count": int(other_sum)})
        else:
            bar_data = [{"category": str(k), "count": int(v)} for k, v in top_cats.items()]

        chart_type = "donut" if len(top_cats) <= 5 else "bar"
        charts.append({
            "id": f"cat_{col}",
            "title": f"Top Categories in {col}",
            "type": chart_type,
            "x_axis": "category",
            "y_axis": "count",
            "data": bar_data
        })

    # --- CHART GENERATOR 4: Bivariate Scatter Plots (Top Correlated Pairs) ---
    if len(numeric_cols) >= 2:
        corr_matrix_df = df_target[numeric_cols].corr().fillna(0).abs()
        pairs = []
        for i in range(len(numeric_cols)):
            for j in range(i + 1, len(numeric_cols)):
                c1, c2 = numeric_cols[i], numeric_cols[j]
                val = corr_matrix_df.loc[c1, c2]
                if not np.isnan(val):
                    pairs.append((c1, c2, val))
        
        pairs.sort(key=lambda x: x[2], reverse=True)

        for c1, c2, score in pairs[:2]:
            sampled_df = df_target[[c1, c2]].dropna().head(150)
            scatter_data = [
                {"x": _sanitize_val(row[c1]), "y": _sanitize_val(row[c2])}
                for _, row in sampled_df.iterrows()
            ]
            charts.append({
                "id": f"scatter_{c1}_vs_{c2}",
                "title": f"Relationship: {c1} vs {c2} (Correlation: {round(score, 2)})",
                "type": "scatter",
                "x_axis": c1,
                "y_axis": c2,
                "data": scatter_data
            })

    # --- CHART GENERATOR 5: Time-Series Trends ---
    if datetime_cols and numeric_cols:
        time_col = datetime_cols[0]
        val_col = numeric_cols[0]
        
        try:
            temp_df = df_target[[time_col, val_col]].dropna().copy()
            temp_df[time_col] = pd.to_datetime(temp_df[time_col], errors='coerce')
            temp_df = temp_df.dropna().sort_values(by=time_col)
            
            if not temp_df.empty:
                span_days = (temp_df[time_col].max() - temp_df[time_col].min()).days
                freq = "D" if span_days <= 90 else ("ME" if span_days <= 1095 else "YE")
                
                time_grouped = temp_df.groupby(pd.Grouper(key=time_col, freq=freq))[val_col].mean().reset_index()
                time_series_data = [
                    {
                        "date": row[time_col].strftime("%Y-%m-%d"),
                        "value": round(float(row[val_col]), 2)
                    }
                    for _, row in time_grouped.head(100).iterrows() if not pd.isna(row[val_col])
                ]

                if time_series_data:
                    charts.append({
                        "id": f"line_trend_{time_col}",
                        "title": f"Trend of {val_col} over Time ({time_col})",
                        "type": "line",
                        "x_axis": "date",
                        "y_axis": "value",
                        "data": time_series_data
                    })
        except Exception:
            pass

    # --- Correlation Heatmap Matrix Payload ---
    formatted_corr = {}
    if len(numeric_cols) >= 2:
        raw_corr = df_target[numeric_cols].corr().round(2)
        formatted_corr = _sanitize_dict(raw_corr.to_dict())

    response_payload = {
        "charts": charts,
        "correlation_matrix": formatted_corr,
        "summary": {
            "total_charts": len(charts),
            "numeric_features": len(numeric_cols),
            "categorical_features": len(categorical_cols),
            "datetime_features": len(datetime_cols),
            "has_missing_data": len(missing_data) > 0
        }
    }

    return _sanitize_dict(response_payload)

def generate_summary_stats(df: pd.DataFrame) -> dict:
    stats = {}
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            stats[col] = {
                "type": "numeric",
                "mean": round(float(df[col].mean()), 2) if not df[col].isnull().all() else None,
                "median": round(float(df[col].median()), 2) if not df[col].isnull().all() else None,
                "missing": int(df[col].isnull().sum())
            }
        else:
            stats[col] = {
                "type": "categorical",
                "unique_values": int(df[col].nunique()),
                "missing": int(df[col].isnull().sum())
            }
    return stats