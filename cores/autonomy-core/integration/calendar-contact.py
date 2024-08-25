import logging
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
import psycopg2
from psycopg2 import sql

# Load environment variables
load_dotenv(
    dotenv_path="/home/ncacord/N.E.X.U.S.-Server/cores/autonomy-core/autonomy.env",
    verbose=True,
    override=True,
)

# Add the parent directory to the Python path
python_path = os.getenv("PYTHONPATH")
if python_path:
    sys.path.append(python_path)

# Now you can import your modules after setting the PYTHONPATH
from calendar_services.calendar_service import add_event, update_event
from contact_management.contact_service import view_contact


# Configure logging
log_file = (
    "/home/ncacord/N.E.X.U.S.-Server/cores/autonomy-core/logs/calendar-contact.log"
)
os.makedirs(os.path.dirname(log_file), exist_ok=True)

# Check if the log file exists, create it if not
if not os.path.exists(log_file):
    with open(log_file, "w") as f:
        pass  # Create the file

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("calendar_contact_logger")

# Fetch PostgreSQL connection details
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")


def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password,
        )
        return conn
    except psycopg2.Error as pe:
        logger.error(f"Error connecting to the database: {str(pe)}")
        return None


def add_contact_birthdays_to_calendar():
    conn = get_db_connection()
    if conn is None:
        return "Failed to connect to the database"

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT contact_id, first_name, last_name, birthday FROM contacts WHERE birthday IS NOT NULL"
            )
            contacts = cursor.fetchall()

            for contact in contacts:
                contact_id, first_name, last_name, birthday = contact
                event_name = f"{first_name} {last_name}'s Birthday"
                event_date = birthday.replace(
                    year=datetime.now().year
                )  # Set event for this year

                # Check if the event already exists
                cursor.execute(
                    "SELECT * FROM events WHERE event_name = %s AND event_date = %s",
                    (event_name, event_date),
                )
                if cursor.fetchone():
                    logger.info(f"Event '{event_name}' already exists in the calendar.")
                else:
                    add_event(event_name, event_date.strftime("%Y-%m-%d"))
                    logger.info(f"Added event '{event_name}' to the calendar.")

    except Exception as e:
        logger.error(f"Error adding birthdays to calendar: {str(e)}")
    finally:
        conn.close()


def update_calendar_events_for_contact(contact_id):
    contact = view_contact(contact_id)
    if isinstance(contact, str):
        logger.error(contact)
        return

    first_name, last_name, birthday = contact[1], contact[2], contact[10]
    event_name = f"{first_name} {last_name}'s Birthday"

    if birthday:
        event_date = birthday.replace(
            year=datetime.now().year
        )  # Set event for this year
        new_event_date_str = event_date.strftime("%Y-%m-%d")
        update_event(event_name, new_event_date_str, new_event_date_str)
        logger.info(f"Updated event '{event_name}' for contact ID {contact_id}.")
    else:
        logger.info(f"No birthday found for contact ID {contact_id}.")


# Example usage
if __name__ == "__main__":
    add_contact_birthdays_to_calendar()
    update_calendar_events_for_contact(1)
