import sqlite3
import pandas as pd
import numpy as np
import os
import pickle
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import roc_auc_score, classification_report
import shap

DB_PATH = os.path.join("data", "analytics.db")
MODEL_PATH = os.path.join("models", "churn_model.pkl")

def train_and_evaluate():
    if not os.path.exists(DB_PATH):
        print("❌ Error: Database not found. Run ingest_data.py first.")
        return

    print("🔄 Loading dataset from SQLite...")
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM raw_customer_360", conn)

    # 1. Identify target column (churn / churned)
    target_col = None
    for possible_target in ['churn', 'churned', 'exited', 'target']:
        if possible_target in df.columns:
            target_col = possible_target
            break

    if not target_col:
        print("⚠️ Target column (churn/churned) not found automatically. Using last numeric column as target.")
        target_col = df.columns[-1]

    print(f"🎯 Target Variable Identified: '{target_col}'")

    # Drop non-predictive ID columns if they exist
    id_cols = [c for c in df.columns if 'id' in c.lower() or 'customer' in c.lower() and c != target_col]
    X = df.drop(columns=[target_col] + id_cols)
    y = df[target_col].astype(int)

    # 2. Preprocess Categorical Variables
    label_encoders = {}
    for col in X.select_dtypes(include=['object', 'category']).columns:
        le = LabelEncoder()
        X[col] = le.fit_transform(X[col].astype(str))
        label_encoders[col] = le

    # Fill missing values
    X = X.fillna(X.median(numeric_only=True))

    # 3. Train-Test Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    # 4. Train Model
    print("🤖 Training Predictive Machine Learning Model...")
    model = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10)
    model.fit(X_train, y_train)

    # 5. Evaluate Model
    y_preds = model.predict(X_test)
    y_probs = model.predict_proba(X_test)[:, 1]
    
    auc = roc_auc_score(y_test, y_probs)
    print(f"✅ Model AUC Score: {auc:.4f}")

    # 6. Generate Predictions for Entire Dataset
    df['risk_score'] = model.predict_proba(X)[:, 1]
    df['risk_tier'] = pd.qcut(df['risk_score'], q=3, labels=['Low Risk', 'Medium Risk', 'High Risk'])

    # Save outputs to SQL database
    df.to_sql("customer_predictions", conn, if_exists="replace", index=False)
    print("✅ Prediction scores and risk tiers saved to SQLite table 'customer_predictions'.")

    # 7. Compute SHAP Explainability Feature Importances
    print("🧠 Calculating SHAP explainability scores...")
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_test)

    # Save model and artifacts
    os.makedirs("models", exist_ok=True)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump({"model": model, "encoders": label_encoders, "features": X.columns.tolist()}, f)
    print(f"💾 Model artifact saved to '{MODEL_PATH}'")

    conn.close()
    print("\n🎉 ML Training & AI Inference Pipeline Complete!")

if __name__ == "__main__":
    train_and_evaluate()