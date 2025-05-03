"""
This script verifies that the PostgreSQL database is running and
accessible before the application starts.
"""

import logging
import psycopg2
from tenacity import retry, stop_after_attempt, wait_fixed, before_log, after_log

from main.core.logger import logger

MAX_TRIES = 60 * 2  # 2 minutes
WAIT_SECONDS = 5

@retry(
    stop=stop_after_attempt(MAX_TRIES),
    wait=wait_fixed(WAIT_SECONDS),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARN),
)
def init() -> None:
    """  
    The function uses the tenacity library for retry logic, attempting to 
    connect for up to 2 minutes with 5-second intervals between attempts.
    """
    # Try different hostnames in order
    hosts_to_try = ["localhost", "db"]
    last_exception = None
    
    for host in hosts_to_try:
        try:
            logger.info(f"Trying to connect to PostgreSQL at {host}")
            conn = psycopg2.connect(
                host=host,
                database="chatbot",
                user="postgres",
                password="postgres",
                port=5432
            )
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            conn.close()
            logger.info(f"Successfully connected to PostgreSQL at {host}")
            return  # Successfully connected, exit the function
        except Exception as e:
            last_exception = e
            logger.warning(f"Failed to connect to {host}: {e}")
    
    # If we get here, all connection attempts failed
    logger.error(f"All connection attempts failed. Last error: {last_exception}")
    raise last_exception

def main() -> None:
    logger.info("Initializing service")
    init()
    logger.info("Service finished initializing")

if __name__ == "__main__":
    main()