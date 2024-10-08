import imaplib
import os
import logging
import json
import time
from dotenv import load_dotenv
from basic_email_tasks import count_unread_emails, automatically_sort_emails
from nlp_email_tasks import summarize_important_emails, detect_email_sentiment
import email

# Load environment variables from the .env file
load_dotenv(
    dotenv_path="/home/ncacord/N.E.X.U.S.-Server/cores/connectivity-core/connectivity.env",
    verbose=True,
    override=True,
)

# Load configuration settings from the config.json file
with open(
    "/home/ncacord/N.E.X.U.S.-Server/cores/connectivity-core/email_management/config.json",
    "r",
) as config_file:
    config = json.load(config_file)

# Fetch email credentials from the environment variables
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = os.getenv("EMAIL_PORT", "")
EMAIL_USER = os.getenv("EMAIL_USER", "")
EMAIL_PASS = os.getenv("EMAIL_PASS", "")

# Setup logging based on the config settings
log_level = getattr(logging, config.get("log_level", "INFO").upper(), logging.INFO)
log_file = (
    "/home/ncacord/N.E.X.U.S.-Server/cores/connectivity-core/logs/email_management.log"
)
os.makedirs(os.path.dirname(log_file), exist_ok=True)

logging.basicConfig(
    filename=log_file,
    level=log_level,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def connect_to_email():
    # Check if all required environment variables are set
    if not all([EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASS]):
        logging.error("Missing one or more required environment variables.")
        return None

    try:
        # Convert port to an integer safely
        port = int(EMAIL_PORT)
    except ValueError:
        logging.error("EMAIL_PORT is not a valid integer.")
        return None

    try:
        # Establish connection to the email server
        mail = imaplib.IMAP4_SSL(EMAIL_HOST, port)
        mail.login(EMAIL_USER, EMAIL_PASS)
        logging.info(f"Connected to {EMAIL_HOST} successfully.")
        return mail
    except imaplib.IMAP4.error as e:
        logging.error(f"IMAP error during connection: {str(e)}")
    except Exception as e:
        logging.error(f"Failed to connect to {EMAIL_HOST}: {str(e)}")

    return None


def disconnect_from_email(mail):
    try:
        if mail:
            mail.logout()
            logging.info("Disconnected from email server.")
    except Exception as e:
        logging.error(f"Failed to disconnect: {str(e)}")


if __name__ == "__main__":
    mail_connection = connect_to_email()
    if mail_connection:
        # Perform any tasks with the mail connection here

        # Basic Tasks
        if not config.get("skip_standard_tasks", False):
            count_unread_emails(mail_connection)
            automatically_sort_emails(mail_connection, config)

        # NLP Tasks
        if not config.get("skip_nlp_tasks", False):
            summarize_important_emails(mail_connection)
            detect_email_sentiment(mail_connection)

        logging.info(
            "All tasks completed. Waiting for 5 seconds before disconnecting..."
        )
        time.sleep(5)  # Wait for 5 seconds

        disconnect_from_email(mail_connection)
