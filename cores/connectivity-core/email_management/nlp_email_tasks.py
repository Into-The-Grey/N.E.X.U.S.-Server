import os
import logging
import email  # Add this line to import the email module
from dotenv import load_dotenv
from transformers import AutoModelForMaskedLM, AutoTokenizer

# Load environment variables from the .env file
load_dotenv(
    dotenv_path="/home/ncacord/N.E.X.U.S.-Server/cores/connectivity-core/connectivity.env"
)

# Load the NLP model path from the environment variables
NLP_MODEL_PATH = os.getenv("NLP_MODEL_PATH", "")

# Load the NLP model
tokenizer = AutoTokenizer.from_pretrained(NLP_MODEL_PATH)
model = AutoModelForMaskedLM.from_pretrained(NLP_MODEL_PATH)


def summarize_important_emails(mail):
    try:
        mail.select("inbox")
        status, response = mail.search(None, "UNSEEN")
        unread_msg_nums = response[0].split()

        for e_id in unread_msg_nums:
            _, msg_data = mail.fetch(e_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject = msg["Subject"]
                    body = get_email_body(msg)  # Function to extract the email body
                    summary = model.summarize(body)
                    logging.info(f"Summary of email '{subject}': {summary}")
    except Exception as e:
        logging.error(f"Failed to summarize important emails: {str(e)}")


def detect_email_sentiment(mail):
    try:
        mail.select("inbox")
        status, response = mail.search(None, "UNSEEN")
        unread_msg_nums = response[0].split()

        for e_id in unread_msg_nums:
            _, msg_data = mail.fetch(e_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject = msg["Subject"]
                    body = get_email_body(msg)  # Function to extract the email body
                    sentiment = model.analyze_sentiment(body)
                    logging.info(f"Sentiment of email '{subject}': {sentiment}")
    except Exception as e:
        logging.error(f"Failed to detect email sentiment: {str(e)}")


def get_email_body(msg):
    # Extract the body from an email message
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                try:
                    return part.get_payload(decode=True).decode(
                        "utf-8", errors="replace"
                    )
                except:
                    return part.get_payload(decode=True).decode(
                        "latin1", errors="replace"
                    )
    else:
        try:
            return msg.get_payload(decode=True).decode("utf-8", errors="replace")
        except:
            return msg.get_payload(decode=True).decode("latin1", errors="replace")
    return ""
