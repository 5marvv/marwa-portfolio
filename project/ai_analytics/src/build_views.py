import sqlite3
import pandas as pd
import os

DB_PATH = os.path.join("data", "analytics.db")

def create_sql_views():
    if not os.path.exists(DB_PATH):
        print(f"❌ Error: Database at '{DB_PATH}' does not exist. Run ingest_data.py first.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    print("🔄 Building SQL Analytical Views...")

    # Fetch column names from raw table to dynamically map features
    cursor.execute("PRAGMA table_info(raw_customer_360);")
    columns = [col[1] for col in cursor.fetchall()]

    # 1. Base Metrics SQL View
    cursor.execute("DROP VIEW IF EXISTS v_customer_summary;")
    view_summary_sql = """
    CREATE VIEW v_customer_summary AS
    SELECT 
        COUNT(*) AS total_customers,
        ROUND(AVG(COALESCE(churn, churned, 0)), 4) * 100 AS churn_rate_pct
    FROM raw_customer_360;
    """
    cursor.execute(view_summary_sql)
    print("  ✅ Created View: 'v_customer_summary'")

    conn.commit()
    conn.close()
    print("\n🎉 SQL Data Modeling Complete!")

if __name__ == "__main__":
    create_sql_views()