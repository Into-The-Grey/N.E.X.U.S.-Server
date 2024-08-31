import imaplib
import os
import logging
import time
import json
import jsoncomment as jsonc
from dotenv import load_dotenv
from basic_email_tasks import count_unread_emails, automatically_sort_emails
from nlp_email_tasks import summarize_important_emails, detect_email_sentiment
from datetime import datetime, timedelta
import email  # Import the email module

# Load environment variables from the .env file
load_dotenv(
    dotenv_path="/home/ncacord/N.E.X.U.S.-Server/cores/connectivity-core/connectivity.env",
    verbose=True,
    override=True,
)

# Load configuration settings from the config.jsonc file
with open(
    "/home/ncacord/N.E.X.U.S.-Server/cores/connectivity-core/config.jsonc", "r"
) as config_file:
    config = jsonc.load(config_file)

# Fetch email credentials from the environment variables
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = os.getenv("EMAIL_PORT", "")
EMAIL_USER = os.getenv("EMAIL_USER", "")
EMAIL_PASS = os.getenv("EMAIL_PASS", "")

# Setup logging
log_file = (
    "/home/ncacord/N.E.X.U.S.-Server/cores/connectivity-core/logs/email_management.log"
)
os.makedirs(os.path.dirname(log_file), exist_ok=True)

logging.basicConfig(
    filename=log_file,
    level=logging.DEBUG,
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


def automatically_sort_emails_custom(mail, sorting_rules, config):
    try:
        if config["only_inbox"]:
            mail.select("inbox")
        else:
            mail.select("all")

        search_criteria = "ALL"
        if config["only_sort_recent"]:
            since_date = (datetime.now() - timedelta(days=1)).strftime("%d-%b-%Y")
            search_criteria = f"(SINCE {since_date})"

        status, response = mail.search(None, search_criteria)
        all_msg_nums = response[0].split()

        for e_id in all_msg_nums:
            _, msg_data = mail.fetch(e_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject = msg["Subject"]
                    from_ = msg.get("From")

                    # Ensure subject and from_ are not None
                    if subject and from_:
                        for rule in sorting_rules:
                            if rule["condition"](subject.lower(), from_.lower()):
                                mail.copy(e_id, rule["folder"])
                                mail.store(e_id, "+FLAGS", "\\Deleted")
                                if not config["in_background"]:
                                    logging.info(
                                        f"Moved email from {from_} with subject '{subject}' to folder '{rule['folder']}'"
                                    )
                                break
        mail.expunge()  # Delete the moved emails from the inbox
    except Exception as e:
        logging.error(f"Failed to sort emails: {str(e)}")


if __name__ == "__main__":
    mail_connection = connect_to_email()
    if mail_connection:
        # Perform any tasks with the mail connection here

        # Basic Tasks
        count_unread_emails(mail_connection)
        automatically_sort_emails_custom(
            mail_connection,
            sorting_rules=[
                {
                    "condition": lambda subject, from_: "invoice" in subject.lower(),
                    "folder": "Invoices",
                },
                {
                    "condition": lambda subject, from_: "newsletter" in subject.lower(),
                    "folder": "Newsletters",
                },
                {
                    "condition": lambda subject, from_: "order confirmation"
                    in subject.lower()
                    or "purchase" in subject.lower(),
                    "folder": "Shopping",
                },
                {
                    "condition": lambda subject, from_: "shipment" in subject.lower()
                    or "tracking" in subject.lower(),
                    "folder": "Shipping",
                },
                {
                    "condition": lambda subject, from_: "game" in subject.lower()
                    or "gaming" in subject.lower(),
                    "folder": "Gaming",
                },
                {
                    "condition": lambda subject, from_: "sale" in subject.lower()
                    or "discount" in subject.lower(),
                    "folder": "Promotions",
                },
                {
                    "condition": lambda subject, from_: "subscription"
                    in subject.lower()
                    or "renewal" in subject.lower(),
                    "folder": "Subscriptions",
                },
                {
                    "condition": lambda subject, from_: "support" in subject.lower()
                    or "help" in subject.lower(),
                    "folder": "Support",
                },
                {
                    "condition": lambda subject, from_: "social" in subject.lower()
                    or "friend request" in subject.lower(),
                    "folder": "Social",
                },
                {
                    "condition": lambda subject, from_: "security alert"
                    in subject.lower()
                    or "password reset" in subject.lower(),
                    "folder": "Security",
                },
            ],
            config=config,
        )

        # NLP Tasks
        summarize_important_emails(mail_connection)
        detect_email_sentiment(mail_connection)

        logging.info(
            "All tasks completed. Waiting for 5 seconds before disconnecting..."
        )
        time.sleep(5)  # Wait for 5 seconds

        disconnect_from_email(mail_connection)
