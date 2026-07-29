# modules/analyzer.py
import pandas as pd
import numpy as np
from typing import Dict, Any, List

def analyze_dataset(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Performs basic statistical analysis and generates natural language business insights safely.
    """
    insights = []
    chart_recommendations = []
    
    if df.empty:
        return {
            "insights": ["The dataset is completely empty."],
            "chart_recommendations": [],
            "summary_statistics": {}
        }
    
    # 1. Classify columns
    # We identify real numeric columns, excluding those that might be IDs or objects
    numeric_cols = []
    categorical_cols = []
    date_cols = []
    
    for col in df.columns:
        # Check if datetime
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            date_cols.append(col)
        # Check if numeric (and not solely empty or boolean)
        elif pd.api.types.is_numeric_dtype(df[col]) and not df[col].dtype == bool:
            numeric_cols.append(col)
        else:
            categorical_cols.append(col)
            
    # 2. Generate categorical column insights
    for col in categorical_cols:
        unique_count = df[col].nunique()
        mode_val = df[col].dropna().mode()
        mode_str = str(mode_val[0]) if not mode_val.empty else "N/A"
        
        insights.append(
            f"The column '{col}' is categorical with {unique_count} unique values. "
            f"The most frequent value is '{mode_str}'."
        )
        
        # Chart recommendation
        if unique_count <= 15:
            chart_recommendations.append({
                "type": "bar",
                "columns": [col],
                "reason": f"To show the distribution of categories in '{col}'."
            })
            chart_recommendations.append({
                "type": "pie",
                "columns": [col],
                "reason": f"To visualize the market share/proportion of '{col}'."
            })

    # 3. Generate numeric column insights safely
    for col in numeric_cols:
        col_clean = df[col].dropna()
        if col_clean.empty:
            continue
            
        mean_val = col_clean.mean()
        min_val = col_clean.min()
        max_val = col_clean.max()
        
        insights.append(
            f"For '{col}': values range from {min_val:,.2f} to {max_val:,.2f} (Average: {mean_val:,.2f})."
        )
        
        # Chart recommendation
        chart_recommendations.append({
            "type": "histogram",
            "columns": [col],
            "reason": f"To view the spread and distribution of values in '{col}'."
        })

    # 4. Correlation Analysis (if we have at least two numeric columns with valid calculations)
    if len(numeric_cols) >= 2:
        try:
            corr_matrix = df[numeric_cols].corr()
            for i in range(len(numeric_cols)):
                for j in range(i + 1, len(numeric_cols)):
                    col1 = numeric_cols[i]
                    col2 = numeric_cols[j]
                    val = corr_matrix.loc[col1, col2]
                    
                    if not pd.isna(val) and abs(val) > 0.4:
                        strength = "strong" if abs(val) > 0.7 else "moderate"
                        direction = "positive" if val > 0 else "negative"
                        insights.append(
                            f"Detected a {strength} {direction} relationship ({val:.2f}) "
                            f"between '{col1}' and '{col2}'."
                        )
                        chart_recommendations.append({
                            "type": "scatter",
                            "columns": [col1, col2],
                            "reason": f"To visualize the relationship and correlation between '{col1}' and '{col2}'."
                        })
        except Exception:
            pass # Fail gracefully if correlation fails due to data constraints
                    
    # 5. Date-based recommendations
    for d_col in date_cols:
        chart_recommendations.append({
            "type": "line",
            "columns": [d_col],
            "reason": f"To view trend patterns over time based on '{d_col}'."
        })

    # Convert describe object output safely to dict
    try:
        summary_stats = df.describe(include='all').replace({np.nan: None}).to_dict()
    except Exception:
        summary_stats = df.describe().replace({np.nan: None}).to_dict()

    return {
        "insights": insights,
        "chart_recommendations": chart_recommendations,
        "summary_statistics": summary_stats
    }

def get_eda_summary(df: pd.DataFrame) -> dict:
    """Generates distribution stats, value counts for top categoricals, and correlation data."""
    numeric_df = df.select_dtypes(include=[np.number])
    categorical_df = df.select_dtypes(include=['object', 'category'])

    # Numeric summaries
    stats = {}
    if not numeric_df.empty:
        for col in numeric_df.columns:
            stats[col] = {
                "mean": round(float(numeric_df[col].mean()), 2),
                "median": round(float(numeric_df[col].median()), 2),
                "min": round(float(numeric_df[col].min()), 2),
                "max": round(float(numeric_df[col].max()), 2),
            }

    # Categorical top value counts
    distributions = {}
    for col in categorical_df.columns:
        top_counts = categorical_df[col].value_counts().head(5).to_dict()
        distributions[col] = [{"name": str(k), "count": int(v)} for k, v in top_counts.items()]

    return {
        "numeric_stats": stats,
        "categorical_distributions": distributions
    }