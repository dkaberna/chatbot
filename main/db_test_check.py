import psycopg2
import os

def check_postgres_connection():
    """Simple synchronous check to test PostgreSQL connectivity"""
    try:
        # Extract host from your DATABASE_URL environment variable or hardcode it
        host = "localhost"  # or get from environment
        conn = psycopg2.connect(
            host=host,
            database="chatbot",
            user="postgres",
            password="postgres",
            port=5432
        )
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        print(f"Successfully connected to database at {host}")
        return True
    except Exception as e:
        print(f"Failed to connect to database: {e}")
        return False

if __name__ == "__main__":
    check_postgres_connection()