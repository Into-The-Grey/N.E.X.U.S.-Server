import logging
import os
from datetime import datetime
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(
    dotenv_path="/home/ncacord/N.E.X.U.S.-Server/cores/autonomy-core/autonomy.env",
    verbose=True,
    override=True,
)

# PostgreSQL database connection details
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")

# Absolute path for the log file
log_file = "/home/ncacord/N.E.X.U.S.-Server/cores/autonomy-core/logs/contact.log"

# Ensure the log directory exists
os.makedirs(os.path.dirname(log_file), exist_ok=True)

# Configure logging
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("cont_logger")


# Function to validate email format
def validate_email(email):
    if "@" not in email or "." not in email.split("@")[-1]:
        return False
    return True


# Function to validate phone number format
def validate_phone(phone):
    if len(phone) < 10 or not phone.isdigit():
        return False
    return True


# Function to establish a database connection
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


# Function to add a contact to the database
def add_contact(
    first_name,
    last_name,
    email,
    phone,
    address=None,
    city=None,
    state=None,
    country=None,
    zip_code=None,
    birthday=None,
    relationship=None,
    profile_picture=None,
    social_media_links=None,
    notes=None,
    tags=None,
    is_favorite=False,
):
    # Validate email and phone number
    if not validate_email(email):
        logger.error(f"Invalid email format: {email}")
        return f"Invalid email format: {email}"
    if not validate_phone(phone):
        logger.error(f"Invalid phone number: {phone}")
        return f"Invalid phone number: {phone}"

    conn = get_db_connection()
    if conn is None:
        return "Failed to connect to the database"

    try:
        with conn.cursor() as cursor:
            insert_query = """
            INSERT INTO contacts (first_name, last_name, email, phone, address, city, state, country, zip_code, birthday, relationship, profile_picture, social_media_links, notes, tags, is_favorite) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(
                insert_query,
                (
                    first_name,
                    last_name,
                    email,
                    phone,
                    address,
                    city,
                    state,
                    country,
                    zip_code,
                    birthday,
                    relationship,
                    profile_picture,
                    social_media_links,
                    notes,
                    tags,
                    is_favorite,
                ),
            )
            conn.commit()
            logger.info(f"Contact '{first_name} {last_name}' added successfully.")
            return f"Contact '{first_name} {last_name}' added successfully."
    except psycopg2.Error as pe:
        logger.error(f"Error adding contact to the database: {str(pe)}")
        return f"Failed to add contact '{first_name} {last_name}' to the database"
    finally:
        conn.close()


# Function to view a contact by ID
def view_contact(contact_id):
    conn = get_db_connection()
    if conn is None:
        return "Failed to connect to the database"

    try:
        with conn.cursor() as cursor:
            select_query = "SELECT * FROM contacts WHERE contact_id = %s"
            cursor.execute(select_query, (contact_id,))
            contact = cursor.fetchone()
            if contact:
                logger.info(f"Contact with ID {contact_id} retrieved successfully.")
                return contact
            else:
                logger.info(f"Contact with ID {contact_id} not found.")
                return f"Contact with ID {contact_id} not found."
    except psycopg2.Error as pe:
        logger.error(f"Error retrieving contact from the database: {str(pe)}")
        return f"Failed to retrieve contact with ID {contact_id}"
    finally:
        conn.close()


# Function to update a contact by ID
def update_contact(contact_id, **kwargs):
    conn = get_db_connection()
    if conn is None:
        return "Failed to connect to the database"

    try:
        # Adding the updated_at field manually
        kwargs["updated_at"] = datetime.now()

        set_clause = ", ".join([f"{key} = %s" for key in kwargs.keys()])
        values = list(kwargs.values()) + [contact_id]

        with conn.cursor() as cursor:
            update_query = f"UPDATE contacts SET {set_clause} WHERE contact_id = %s"
            cursor.execute(update_query, values)
            conn.commit()
            logger.info(f"Contact with ID {contact_id} updated successfully.")
            return f"Contact with ID {contact_id} updated successfully."
    except psycopg2.Error as pe:
        logger.error(f"Error updating contact in the database: {str(pe)}")
        return f"Failed to update contact with ID {contact_id}"
    finally:
        conn.close()


# Function to delete a contact by ID
def delete_contact(contact_id):
    conn = get_db_connection()
    if conn is None:
        return "Failed to connect to the database"

    try:
        with conn.cursor() as cursor:
            delete_query = "DELETE FROM contacts WHERE contact_id = %s"
            cursor.execute(delete_query, (contact_id,))
            conn.commit()
            logger.info(f"Contact with ID {contact_id} deleted successfully.")
            return f"Contact with ID {contact_id} deleted successfully."
    except psycopg2.Error as pe:
        logger.error(f"Error deleting contact from the database: {str(pe)}")
        return f"Failed to delete contact with ID {contact_id}"
    finally:
        conn.close()


# Function to search contacts by a given field and value
def search_contacts(field, value):
    conn = get_db_connection()
    if conn is None:
        return "Failed to connect to the database"

    try:
        with conn.cursor() as cursor:
            search_query = sql.SQL("SELECT * FROM contacts WHERE {} = %s").format(
                sql.Identifier(field)
            )
            cursor.execute(search_query, (value,))
            contacts = cursor.fetchall()
            if contacts:
                logger.info(
                    f"Found {len(contacts)} contact(s) matching {field} = {value}"
                )
                return contacts
            else:
                logger.info(f"No contacts found matching {field} = {value}")
                return f"No contacts found matching {field} = {value}"
    except psycopg2.Error as pe:
        logger.error(f"Error searching contacts in the database: {str(pe)}")
        return f"Failed to search contacts by {field} = {value}"
    finally:
        conn.close()


# Function to list all contacts
def list_contacts():
    conn = get_db_connection()
    if conn is None:
        return "Failed to connect to the database"

    try:
        with conn.cursor() as cursor:
            select_query = "SELECT * FROM contacts"
            cursor.execute(select_query)
            contacts = cursor.fetchall()
            if contacts:
                logger.info(f"Retrieved {len(contacts)} contacts.")
                return contacts
            else:
                logger.info("No contacts found.")
                return "No contacts found."
    except psycopg2.Error as pe:
        logger.error(f"Error retrieving contacts from the database: {str(pe)}")
        return "Failed to retrieve contacts"
    finally:
        conn.close()


# Function to list all favorite contacts
def list_favorite_contacts():
    conn = get_db_connection()
    if conn is None:
        return "Failed to connect to the database"

    try:
        with conn.cursor() as cursor:
            select_query = "SELECT * FROM contacts WHERE is_favorite = TRUE"
            cursor.execute(select_query)
            contacts = cursor.fetchall()
            if contacts:
                logger.info(f"Retrieved {len(contacts)} favorite contacts.")
                return contacts
            else:
                logger.info("No favorite contacts found.")
                return "No favorite contacts found."
    except psycopg2.Error as pe:
        logger.error(f"Error retrieving favorite contacts from the database: {str(pe)}")
        return "Failed to retrieve favorite contacts"
    finally:
        conn.close()
