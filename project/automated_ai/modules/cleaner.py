# modules/cleaner.py
import pandas as pd
from typing import Dict, Any, List, Tuple

def remove_duplicates(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """
    Removes duplicate rows from the DataFrame.
    Returns the cleaned DataFrame and the number of rows removed.
    """
    initial_rows = len(df)
    df_cleaned = df.drop_duplicates()
    removed = initial_rows - len(df_cleaned)
    return df_cleaned, removed

def handle_missing_values(
    df: pd.DataFrame, 
    column: str, 
    strategy: str, 
    fill_value: Any = None
) -> pd.DataFrame:
    """
    Handles missing values in a specific column based on the selected strategy.
    Strategies: 'drop_rows', 'drop_column', 'mean', 'median', 'mode', 'constant'
    """
    df = df.copy()
    
    if strategy == 'drop_rows':
        df = df.dropna(subset=[column])
    elif strategy == 'drop_column':
        df = df.drop(columns=[column])
    elif strategy == 'mean':
        if pd.api.types.is_numeric_dtype(df[column]):
            df[column] = df[column].fillna(df[column].mean())
    elif strategy == 'median':
        if pd.api.types.is_numeric_dtype(df[column]):
            df[column] = df[column].fillna(df[column].median())
    elif strategy == 'mode':
        mode_val = df[column].mode()
        if not mode_val.empty:
            df[column] = df[column].fillna(mode_val[0])
    elif strategy == 'constant' and fill_value is not None:
        df[column] = df[column].fillna(fill_value)
        
    return df

def cast_column_type(df: pd.DataFrame, column: str, target_type: str) -> pd.DataFrame:
    """
    Safely converts a column to a specified target data type.
    Target types: 'int', 'float', 'str', 'datetime'
    """
    df = df.copy()
    try:
        if target_type == 'int':
            df[column] = pd.to_numeric(df[column], errors='coerce').astype('Int64')
        elif target_type == 'float':
            df[column] = pd.to_numeric(df[column], errors='coerce').astype(float)
        elif target_type == 'str':
            df[column] = df[column].astype(str)
        elif target_type == 'datetime':
            df[column] = pd.to_datetime(df[column], errors='coerce')
    except Exception as e:
        raise ValueError(f"Failed to convert column '{column}' to {target_type}: {str(e)}")
        
    return df