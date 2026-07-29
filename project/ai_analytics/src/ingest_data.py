import sqlite3
import pandas as pd
import os

# Paths setup
DATA_PATH = os.path.join("data", "customer_data.csv")
DB_PATH = os.path.join("data", "analytics.db")

def setup_database():
    if not os.path.exists(DATA_PATH):
        print(f"❌ Error: {DATA_PATH} not found. Please make sure customer_data.csv is inside your 'data' folder!")
        return

    print("🔄 Ingesting 360° customer dataset...")
    df = pd.read_csv(DATA_PATH)

    # Standardize column names (lowercase, replace spaces/dashes with underscores)
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_").str.replace("-", "_")

    # Connect to SQLite Database
    conn = sqlite3.connect(DB_PATH)
    
    # Store raw data into database table
    df.to_sql("raw_customer_360", conn, if_exists="replace", index=False)
    print("✅ Raw dataset successfully stored in table 'raw_customer_360'")

    print(f"\n📊 Total Records: {len(df):,}")
    print("📋 Columns Available for Analysis:")
    for col in df.columns:
        print(f"  • {col}")

    conn.close()
    print(f"\n🎉 Database created successfully at '{DB_PATH}'!")

if __name__ == "__main__":
    setup_database()