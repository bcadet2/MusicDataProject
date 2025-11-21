# scripts/db_connection.py
import os
import psycopg2
from dotenv import load_dotenv

def get_connection():
    """Get PostgreSQL connection to Neon database."""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL not set in environment")
    return psycopg2.connect(database_url)

def test_connection():
    """Test database connection."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT version()")
            print(cur.fetchone())
    finally:
        conn.close()

if __name__ == "__main__":
    test_connection()
