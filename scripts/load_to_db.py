import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import os

# 📂 Use a raw string (r"...") for the Windows path
# This path is now constructed to be relative to the script's location
script_dir = os.path.dirname(__file__)
CSV_PATH = os.path.join(script_dir, '..', 'data', 'cleaned_data.csv')


# 🛠️ PostgreSQL credentials (make sure these match your new installation)
DB_NAME = "clickstreamdb"
DB_USER = "postgres"
DB_PASSWORD = "utsab" # Or the new password you set
DB_HOST = "localhost"
DB_PORT = "5432"

def insert_into_db(df, table_name, conn):
    cursor = conn.cursor()
    # Create schema if it doesn't exist
    cursor.execute("CREATE SCHEMA IF NOT EXISTS clickstream;")
    # Create table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clickstream.shopper_data (
            administrative INT,
            administrative_duration FLOAT,
            informational INT,
            informational_duration FLOAT,
            productrelated INT,
            productrelated_duration FLOAT,
            bouncerates FLOAT,
            exitrates FLOAT,
            pagevalues FLOAT,
            specialday FLOAT,
            month VARCHAR(20),
            operatingsystems INT,
            browser INT,
            region INT,
            traffictype INT,
            visitortype VARCHAR(50),
            weekend BOOLEAN,
            revenue BOOLEAN
        );
    """)
    
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

    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        insert_into_db(df, "shopper_data", conn)
        conn.close()
    except psycopg2.OperationalError as e:
        print(f"❌ DATABASE CONNECTION FAILED: {e}")
        print("👉 Please ensure PostgreSQL is running and your credentials in the script are correct.")


if __name__ == "__main__":
    main()