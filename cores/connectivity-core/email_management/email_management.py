import imaplib
import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv(
    dotenv_path="/home/ncacord/N.E.X.U.S.-Server/cores/connectivity-core/connectivity.env",
    verbose=True,
    override=True,
)

# Fetch email credentials from the environment variables
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = os.getenv("EMAIL_PORT", "")
EMAIL_USER = os.getenv("EMAIL_USER", "")
EMAIL_PASS = os.getenv("EMAIL_PASS", "")


def connect_to_email():
    # Check if all required environment variables are set
    if not all([EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASS]):
        print("Error: Missing one or more required environment variables.")
        return None

    try:
        # Convert port to an integer safely
        port = int(EMAIL_PORT)
    except ValueError:
        print("Error: EMAIL_PORT is not a valid integer.")
        return None

    try:
        # Establish connection to the email server
        mail = imaplib.IMAP4_SSL(EMAIL_HOST, port)
        mail.login(EMAIL_USER, EMAIL_PASS)
        print(f"Connected to {EMAIL_HOST} successfully.")
        return mail
    except imaplib.IMAP4.error as e:
        print(f"IMAP error during connection: {str(e)}")
    except Exception as e:
        print(f"Failed to connect to {EMAIL_HOST}: {str(e)}")

    return None


def disconnect_from_email(mail):
    try:
        if mail:
            mail.logout()
            print("Disconnected from email server.")
    except Exception as e:
        print(f"Failed to disconnect: {str(e)}")


if __name__ == "__main__":
    # Example usage
    mail_connection = connect_to_email()
    if mail_connection:
        disconnect_from_email(mail_connection)
