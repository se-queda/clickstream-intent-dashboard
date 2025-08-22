import pandas as pd
import os

RAW_PATH = "/home/utsab/Desktop/clickstream/data/raw/online_shoppers_intention.csv"
CLEAN_PATH = "/home/utsab/Desktop/clickstream/data/raw/cleaned_data.csv"

def load_and_clean():
    print("📥 Loading raw CSV...")
    df = pd.read_csv(RAW_PATH)

    print("🧪 Raw columns:", df.columns.tolist())

    # Normalize column names
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
    print("✅ Normalized columns:", df.columns.tolist())

    # Fix data types
    df['month'] = df['month'].astype(str)
    df['visitortype'] = df['visitortype'].astype(str)  # 🛠️ THIS is the correct name
    df['weekend'] = df['weekend'].astype(bool)
    df['revenue'] = df['revenue'].astype(bool)

    # Optional: handle missing values if needed
    df.dropna(inplace=True)

    # Save cleaned data
    os.makedirs("../data", exist_ok=True)
    df.to_csv(CLEAN_PATH, index=False)
    print(f"✅ Cleaned data saved to {CLEAN_PATH} with {len(df)} rows.")

if __name__ == "__main__":
    load_and_clean()

