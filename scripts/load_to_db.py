import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

# 📂 Path to your cleaned CSV
CSV_PATH = "../data/raw/cleaned_data.csv"

# 🛠️ PostgreSQL credentials
DB_NAME = "clickstreamdb"
DB_USER = "postgres"
DB_PASSWORD = "utsab"
DB_HOST = "localhost"
DB_PORT = "5432"

def insert_into_db(df, table_name, conn):
    cursor = conn.cursor()
    cols = ','.join(df.columns)
    values = [tuple(row) for row in df.to_numpy()]
    query = f"INSERT INTO clickstream.{table_name} ({cols}) VALUES %s"


    try:
        execute_values(cursor, query, values)
        conn.commit()
        print(f"✅ Inserted {len(df)} rows into clickstream.{table_name}")
    except Exception as e:
        print(f"❌ Insert error: {e}")
        conn.rollback()
    finally:
        cursor.close()

def main():
    print("📥 Loading cleaned CSV...")
    df = pd.read_csv(CSV_PATH)

    # 🧼 Convert booleans
    df['weekend'] = df['weekend'].astype(bool)
    df['revenue'] = df['revenue'].astype(bool)

    print(f"📊 Rows to insert: {len(df)}")

    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )

    insert_into_db(df, "shopper_data", conn)
    conn.close()

if __name__ == "__main__":
    main()

