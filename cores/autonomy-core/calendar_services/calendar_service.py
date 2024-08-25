import logging
import os
from datetime import datetime
import psycopg2
from dotenv import load_dotenv
from psycopg2 import pool
from regex import D

# Load environment variables from .env file
load_dotenv(dotenv_path="/home/ncacord/N.E.X.U.S.-Server/cores/autonomy-core/autonomy.env", verbose=True, override=True)

# PostgreSQL database connection details
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")

# Absolute path for the log file
log_file = "/home/ncacord/N.E.X.U.S.-Server/cores/autonomy-core/logs/calendar.log"

# Ensure the log directory exists
os.makedirs(os.path.dirname(log_file), exist_ok=True)

# Configure logging to use the specified absolute path
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("cal_logger")


# Function to add an event to the calendar
def add_event(event_name, event_date_str):
    try:
        # Parse the event date
        event_date = datetime.strptime(event_date_str, "%Y-%m-%d").date()

        # Create a connection pool if it doesn't exist
        if "connection_pool" not in globals():
            global connection_pool
            connection_pool = pool.SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                host=db_host,
                port=db_port,
                database=db_name,
                user=db_user,
                password=db_password,
            )

        # Get a connection from the pool
        conn = connection_pool.getconn()

        try:
            with conn.cursor() as cursor:
                insert_query = """
                INSERT INTO events (event_name, event_date) 
                VALUES (%s, %s)
                """
                cursor.execute(insert_query, (event_name, event_date))
                conn.commit()

        finally:
            # Return the connection to the pool
            connection_pool.putconn(conn)

        logger.info(f"Event '{event_name}' added for {event_date}")
    except psycopg2.Error as pe:
        logger.error(f"Error adding event to database: {str(pe)}")
    except ValueError as ve:
        logger.error(f"Error parsing date: {str(ve)}")
    except Exception as e:
        logger.error(f"Error adding event: {str(e)}")


# Function to view upcoming events
def view_events():
    try:
        with psycopg2.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password,
        ) as conn:
            with conn.cursor() as cursor:
                select_query = """
                SELECT event_name, event_date 
                FROM events 
                ORDER BY event_date ASC
                """
                cursor.execute(select_query)
                rows = cursor.fetchall()

        if not rows:
            logger.info("No upcoming events")
            return "No upcoming events."

        events = []
        for event_name, event_date in rows:
            event_entry = f"{event_name} on {event_date.strftime('%A, %B %d, %Y')}"
            events.append(event_entry)

        logger.info("Retrieving upcoming events")
        return "\n".join(events)
    except psycopg2.Error as pe:
        logger.error(f"Error retrieving events from database: {str(pe)}")
        return "Failed to retrieve events from the database"
    except Exception as se:
        logger.error(f"Failed to retrieve events: {str(se)}")
        return f"Failed to retrieve events: {str(se)}"

# Function to update an event
def update_event(event_id, new_event_name, new_event_date_str):
    try:
        # Parse the new event date
        new_event_date = datetime.strptime(new_event_date_str, "%Y-%m-%d").date()

        with psycopg2.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password,
        ) as conn:
            with conn.cursor() as cursor:
                update_query = """
                UPDATE events 
                SET event_name = %s, event_date = %s 
                WHERE event_id = %s
                """
                cursor.execute(update_query, (new_event_name, new_event_date, event_id))
                conn.commit()

        logger.info(f"Event with ID {event_id} updated to '{new_event_name}' on {new_event_date}")
        return f"Event with ID {event_id} updated successfully."
    except psycopg2.Error as pe:
        logger.error(f"Error updating event in database: {str(pe)}")
        return "Failed to update event in the database"
    except ValueError as ve:
        logger.error(f"Error parsing date: {str(ve)}")
        return "Failed to update event: Invalid date format"
    except Exception as e:
        logger.error(f"Error updating event: {str(e)}")
        return "Failed to update event"
    