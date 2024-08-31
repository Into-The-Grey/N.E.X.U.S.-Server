import imaplib
import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv(dotenv_path="/home/ncacord/N.E.X.U.S.-Server/cores/connectivity-core/connectivity.env", verbose=True, 
override=True)

# Fetch email credentials from the environment variables
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", ""))
EMAIL_USER = os.getenv("EMAIL_USER", "")
EMAIL_PASS = os.getenv("EMAIL_PASS", "")


def connect_to_email():
    mail = None  # Initialize mail variable
    try:
        # Establish connection to the email server
        if EMAIL_HOST is not None and EMAIL_PORT is not None:
            mail = imaplib.IMAP4_SSL(EMAIL_HOST, int(EMAIL_PORT))
            if EMAIL_USER is not None and EMAIL_PASS is not None:
                if mail.login(EMAIL_USER, EMAIL_PASS):
                    print(f"Connected to {EMAIL_HOST} successfully.")
                    return mail
        print(f"Failed to connect to {EMAIL_HOST}")
        return None
    except Exception as e:
        print(f"Failed to connect to {EMAIL_HOST}: {str(e)}")
        return None


def disconnect_from_email(mail):
    try:
        if mail is not None:
            mail.logout()
            print("Disconnected from email server.")
    except Exception as e:
        print(f"Failed to disconnect: {str(e)}")


if __name__ == "__main__":
    # Example usage
    mail_connection = connect_to_email()
    if mail_connection:
        disconnect_from_email(mail_connection)
