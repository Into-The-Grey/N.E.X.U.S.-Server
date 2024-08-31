import imaplib
import os
import logging
import email
from email.message import EmailMessage
from email.policy import default as email_policy_default
from dotenv import load_dotenv
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import json
import re

# Load environment variables from the .env file
load_dotenv(
    dotenv_path="/home/ncacord/N.E.X.U.S.-Server/cores/connectivity-core/connectivity.env",
    verbose=True,
    override=True,
)

# Load the NLP model path from the environment variables
SEQ2SEQ_MODEL_PATH = os.getenv("SEQ2SEQ_MODEL_PATH")
if SEQ2SEQ_MODEL_PATH is None:
    raise ValueError("SEQ2SEQ_MODEL_PATH environment variable is not set.")

# Load the NLP model
tokenizer = AutoTokenizer.from_pretrained(SEQ2SEQ_MODEL_PATH)
model = AutoModelForSeq2SeqLM.from_pretrained(SEQ2SEQ_MODEL_PATH)

# Load configuration settings from the config.json file
try:
    with open(
        "/home/ncacord/N.E.X.U.S.-Server/cores/connectivity-core/email_management/config.json",
        "r",
    ) as config_file:
        config = json.load(config_file)
except Exception as e:
    logging.error(f"Failed to load configuration from config.json: {str(e)}")
    config = {}


# Function to clean and sanitize email headers
def clean_header(header, value):
    """
    Cleans and sanitizes email header values by removing invalid characters.
    """
    if not value:
        return None
    # Remove linefeeds and carriage returns
    value = value.replace("\n", "").replace("\r", "")
    # Replace invalid characters with a placeholder
    value = re.sub(r"[^\x20-\x7E]", "", value)  # Keep only printable ASCII characters
    if not value:
        logging.warning(f"Header '{header}' was empty after sanitization.")
        return None
    return value


def convert_to_email_message(msg):
    """Convert a general Message object to an EmailMessage object."""
    if not isinstance(msg, EmailMessage):
        new_msg = EmailMessage(policy=email_policy_default)
        for header, value in msg.items():
            cleaned_value = clean_header(header, value)
            if cleaned_value:
                try:
                    new_msg[header] = cleaned_value
                except ValueError as e:
                    logging.error(f"Failed to set header '{header}': {str(e)}")
            else:
                logging.warning(
                    f"Skipping header '{header}' due to invalid characters."
                )
        new_msg.set_payload(msg.get_payload())
        msg = new_msg
    return msg


def summarize_important_emails(mail):
    if config.get("skip_summarization", False):
        logging.info("Summarization skipped as per configuration.")
        return

    try:
        mail.select("inbox")
        status, response = mail.search(None, "UNSEEN")
        unread_msg_nums = response[0].split() if response[0] else []

        for e_id in unread_msg_nums:
            _, msg_data = mail.fetch(e_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    msg = convert_to_email_message(
                        msg
                    )  # Convert the msg to EmailMessage
                    subject = msg["Subject"]
                    body = get_email_body(msg)  # Function to extract the email body

                    # Ensure that body is a string before slicing
                    if isinstance(body, str):
                        # Tokenize the input
                        inputs = tokenizer.encode(
                            "summarize: "
                            + body[: config.get("max_email_body_length", 512)],
                            return_tensors="pt",
                            max_length=config.get("max_email_body_length", 512),
                            truncation=True,
                        )

                        # Generate the summary
                        summary_ids = model.generate(
                            inputs,
                            max_length=config.get("max_summary_length", 100),
                            num_beams=config.get("num_beams", 4),
                            no_repeat_ngram_size=config.get("no_repeat_ngram_size", 2),
                            early_stopping=config.get("early_stopping", True),
                        )
                        summary = tokenizer.decode(
                            summary_ids[0], skip_special_tokens=True
                        )

                        logging.info(f"Summary of email '{subject}': {summary}")
    except Exception as e:
        logging.error(f"Failed to summarize important emails: {str(e)}")


def detect_email_sentiment(mail):
    if config.get("skip_sentiment_analysis", False):
        logging.info("Sentiment analysis skipped as per configuration.")
        return

    try:
        mail.select("inbox")
        status, response = mail.search(None, "UNSEEN")
        unread_msg_nums = response[0].split() if response[0] else []

        for e_id in unread_msg_nums:
            _, msg_data = mail.fetch(e_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    msg = convert_to_email_message(
                        msg
                    )  # Convert the msg to EmailMessage
                    subject = msg["Subject"]
                    body = get_email_body(msg)  # Function to extract the email body

                    # Ensure that body is a string before tokenization
                    if isinstance(body, str):
                        # Tokenize the input
                        inputs = tokenizer(
                            body,
                            return_tensors="pt",
                            max_length=config.get("max_email_body_length", 512),
                            truncation=True,
                        )

                        # Perform sentiment analysis (assuming you have a suitable classification model)
                        outputs = model(**inputs)
                        sentiment = outputs.logits.argmax(dim=1).item()

                        sentiment_labels = config.get(
                            "sentiment_labels",
                            [
                                "Negative",
                                "Positive",
                                "Neutral",
                                "Mixed",
                                "Unknown",
                                "Error",
                                "Not Applicable",
                            ],
                        )
                        logging.info(
                            f"Sentiment of email '{subject}': {sentiment_labels[sentiment]}"
                        )
    except Exception as e:
        logging.error(f"Failed to detect email sentiment: {str(e)}")


def get_email_body(msg):
    if isinstance(msg, EmailMessage):
        body = []
        if msg.is_multipart():
            for part in msg.iter_parts():
                if part.get_content_type() == "text/plain":
                    try:
                        payload = part.get_payload(decode=True)
                        if isinstance(payload, bytes):
                            body.append(payload.decode("utf-8", errors="replace"))
                        else:
                            body.append(payload)
                    except Exception as e:
                        logging.error(f"Failed to decode part: {str(e)}")
        else:
            try:
                payload = msg.get_payload(decode=True)
                if isinstance(payload, bytes):
                    body.append(payload.decode("utf-8", errors="replace"))
                else:
                    body.append(payload)
            except Exception as e:
                logging.error(f"Failed to decode payload: {str(e)}")
        return "\n".join(body)
    else:
        raise TypeError(
            f"msg is not an instance of EmailMessage, actual type: {type(msg).__name__}"
        )


# Example usage
# Call your functions with the appropriate mail object as needed
