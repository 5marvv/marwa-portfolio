# modules/ml.py
import os
import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, r2_score, mean_squared_error
from typing import Dict, Any

MODELS_DIR = os.path.join("data", "models")
os.makedirs(MODELS_DIR, exist_ok=True)

def auto_train_model(df: pd.DataFrame, target_column: str, model_name: str = "default_model") -> Dict[str, Any]:
    """
    Trains a model, saves it to data/models/, and returns performance metrics.
    """
    if target_column not in df.columns:
        raise ValueError(f"Target column '{target_column}' not found in dataset.")
        
    df_ml = df.copy().dropna(subset=[target_column])
    
    # 1. Task Detection
    is_numeric = pd.api.types.is_numeric_dtype(df_ml[target_column])
    unique_count = df_ml[target_column].nunique()
    
    if is_numeric and unique_count > 2:
        task_type = "regression"
    else:
        task_type = "classification"
        
    # 2. Preprocess Features
    y = df_ml[target_column]
    X = df_ml.drop(columns=[target_column])
    
    label_encoders = {}
    
    # Process Target if Classification
    target_encoder = None
    if task_type == "classification" and not pd.api.types.is_numeric_dtype(y):
        target_encoder = LabelEncoder()
        y = target_encoder.fit_transform(y.astype(str))
        
    for col in X.columns:
        if pd.api.types.is_numeric_dtype(X[col]):
            X[col] = X[col].fillna(X[col].median())
        else:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str).fillna("Unknown"))
            label_encoders[col] = le

    # 3. Train-Test Split
    test_size = 0.2 if len(df_ml) > 10 else 0.4
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42
    )
    
    # 4. Train Model
    feature_names = X.columns.tolist()
    
    if task_type == "classification":
        model = RandomForestClassifier(n_estimators=50, random_state=42)
        model.fit(X_train, y_train)
        predictions = model.predict(X_test)
        metrics = {
            "accuracy": float(accuracy_score(y_test, predictions)),
            "metric_name": "Accuracy",
            "metric_value": f"{accuracy_score(y_test, predictions) * 100:.2f}%"
        }
    else:
        model = RandomForestRegressor(n_estimators=50, random_state=42)
        model.fit(X_train, y_train)
        predictions = model.predict(X_test)
        r2 = r2_score(y_test, predictions)
        metrics = {
            "r2_score": float(r2),
            "metric_name": "R² (Variance Explained)",
            "metric_value": f"{r2:.4f}"
        }
        
    # 5. Extract Feature Importances
    importances = model.feature_importances_
    importance_list = sorted(
        [{"feature": name, "importance": float(imp)} for name, imp in zip(feature_names, importances)],
        key=lambda x: x["importance"],
        reverse=True
    )
    
    # 6. Save the model bundle to disk
    model_bundle = {
        "model": model,
        "task_type": task_type,
        "feature_names": feature_names,
        "label_encoders": label_encoders,
        "target_encoder": target_encoder,
        "target_column": target_column
    }
    
    save_path = os.path.join(MODELS_DIR, f"{model_name}.joblib")
    joblib.dump(model_bundle, save_path)
    
    return {
        "task_type": task_type,
        "target_column": target_column,
        "metrics": metrics,
        "feature_importances": importance_list,
        "saved_model_path": save_path
    }