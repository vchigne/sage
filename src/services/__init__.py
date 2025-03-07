"""
SAGE Services Module
Contains data processing and validation services
"""
import os
import psycopg2
import logging

def setup_database_connection(database_url=None):
    """Setup database connection using environment variables or provided URL"""
    try:
        if database_url is None:
            database_url = os.environ.get('DATABASE_URL')

        if database_url is None:
            raise ValueError("No database URL provided")

        connection = psycopg2.connect(database_url)
        connection.autocommit = True
        logging.info("Database connection established")
        return connection
    except Exception as e:
        logging.error(f"Error connecting to database: {str(e)}")
        return None