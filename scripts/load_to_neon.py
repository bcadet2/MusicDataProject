# scripts/load_to_neon.py
import os
import psycopg2
import csv
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / "env" / "discogs.env")

def get_db_connection():
    database_url = os.getenv('DATABASE_URL')
    return psycopg2.connect(database_url)

def load_artists():
    # Load artists.csv to database
    pass

def load_songs():
    # Load songs.csv to database
    pass

def main():
    conn = get_db_connection()
    try:
        # Load all your CSV data
        load_artists()
        load_songs()
        # etc.
    finally:
        conn.close()

if __name__ == "__main__":
    main()
