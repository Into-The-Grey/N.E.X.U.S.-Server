import os
from datetime import datetime
import psycopg2
from dotenv import load_dotenv
from logger import logger  # Importing the logger from the logger module

# Load environment variables from .env file
load_dotenv()

# PostgreSQL database connection details
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")

# Log path
log_path = "/home/ncacord/N.E.X.U.S.-Server/cores/autonomy-core/logging/calendar.log"

# Function to create the necessary tables if they don't exist
def create_tables():
    try:
        # Establish database connection
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password,
        )
        cursor = conn.cursor()

        # Create 'events' table if it doesn't exist
        create_table_query = """
        CREATE TABLE IF NOT EXISTS events (
            event_id SERIAL PRIMARY KEY,
            event_name VARCHAR(255) NOT NULL,
            event_description TEXT,
            event_categories VARCHAR(255)[],
            event_date DATE NOT NULL,
            event_date_timestamp INT,
            event_start_time TIMESTAMP,
            event_end_time TIMESTAMP,
            is_featured BOOLEAN DEFAULT FALSE,
            is_multi_day BOOLEAN DEFAULT FALSE,
            is_past_event BOOLEAN DEFAULT FALSE,
            is_today BOOLEAN DEFAULT FALSE,
            published_on_date DATE,
            published_on_time TIME,
            published_on_timestamp INT,
            registration_info JSON,
            repeat_data JSON,
            spans_multiple_days BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            contact_id INT REFERENCES contacts(contact_id) ON DELETE CASCADE
        )
        """
        cursor.execute(create_table_query)
        conn.commit()

        logger.info("Tables created successfully")
    except psycopg2.Error as pe:
        logger.error(f"Error creating tables: {str(pe)}")
    except Exception as e:
        logger.error(f"Error creating tables: {str(e)}")


# Function to add an event to the calendar
def add_event(event_name, event_date):
    try:
        # Establish database connection
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password,
        )
        cursor = conn.cursor()

        # Assuming event_date is a string in 'YYYY-MM-DD' format
        event_datetime = datetime.strptime(event_date, "%Y-%m-%d")

        # Insert event into the database
        insert_query = """
        INSERT INTO events (event_name, event_date) 
        VALUES (%s, %s)
        """
        cursor.execute(insert_query, (event_name, event_datetime))
        conn.commit()

        logger.info(f"Event '{event_name}' added for {event_date}")
        return f"Event '{event_name}' has been scheduled for {event_datetime.strftime('%A, %B %d, %Y')}"
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
        # Establish database connection
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password,
        )
        cursor = conn.cursor()

        # Retrieve upcoming events from the database
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
        for row in rows:
            event_name, event_date = row
            event_entry = f"{event_name} on {event_date.strftime('%A, %B %d, %Y')}"
            events.append(event_entry)

        logger.info("Retrieving upcoming events")
        return "\n".join(events)
    except psycopg2.Error as pe:
        logger.error(f"Error retrieving events from database: {str(pe)}")
        return "Failed to retrieve events from the database"
    except Exception as se:
        logger.error(f"Error viewing events: {str(se)}")
        return "Failed to retrieve events: {str(se)}"


# Create tables if they don't exist
create_tables()

# Example usage
if __name__ == "__main__":
    print(add_event("Project Deadline", "2024-09-01"))
    print(view_events())
