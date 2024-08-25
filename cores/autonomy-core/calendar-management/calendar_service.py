import os
from datetime import datetime
import psycopg2
from dotenv import load_dotenv
from logger import logger  # Importing the logger from the logger module

# Load environment variables from .env file
load_dotenv()

# PostgreSQL database connection detailsSELECT successfully executed.
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")

# Log path
log_path = "/home/ncacord/N.E.X.U.S.-Server/cores/autonomy-core/logging/calendar.log"

# Create log directory if it doesn't exist
os.makedirs(os.path.dirname(log_path), exist_ok=True)

# Check if the log file exists, create it if not
if not os.path.exists(log_path):
    with open(log_path, "w") as log_file:
        log_file.write("")  # Create an empty log file


# Function to add an event to the calendar
def add_event(event_name, event_date_str):
    try:
        # Parse the event date
        event_date = datetime.strptime(event_date_str, "%Y-%m-%d").date()

        with psycopg2.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password,
        ) as conn:
            with conn.cursor() as cursor:
                insert_query = """
                INSERT INTO events (event_name, event_date) 
                VALUES (%s, %s)
                """
                cursor.execute(insert_query, (event_name, event_date))
                conn.commit()

        logger.info(f"Event '{event_name}' added for {event_date}")
        return f"Event '{event_name}' has been scheduled for {event_date.strftime('%A, %B %d, %Y')}"
    except psycopg2.Error as pe:
        logger.error(f"Error adding event to database: {str(pe)}")
        return f"Failed to add event '{event_name}' to the database"
    except ValueError as ve:
        logger.error(f"Error parsing date: {str(ve)}")
        return f"Failed to add event '{event_name}': Invalid date format"
    except Exception as e:
        logger.error(f"Error adding event: {str(e)}")
        return f"Failed to add event '{event_name}'"


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


# Example usage
if __name__ == "__main__":
    print(view_events())
