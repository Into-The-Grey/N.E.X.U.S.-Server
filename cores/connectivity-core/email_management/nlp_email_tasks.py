import os
import logging
import email  # Import the email module
from dotenv import load_dotenv
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import jsoncomment as jsonc  # Import the jsoncomment module

# Load environment variables from the .env file
load_dotenv(
    dotenv_path="/home/ncacord/N.E.X.U.S.-Server/cores/connectivity-core/connectivity.env"
)

# Load the NLP model path from the environment variables
NLP_MODEL_PATH = os.getenv("NLP_MODEL_PATH", "")

# Load the NLP model
tokenizer = AutoTokenizer.from_pretrained(NLP_MODEL_PATH)
model = AutoModelForSeq2SeqLM.from_pretrained(NLP_MODEL_PATH)

# Load configuration settings from the config.jsonc file
with open(
    "/home/ncacord/N.E.X.U.S.-Server/cores/connectivity-core/config.jsonc", "r"
) as config_file:
    config = jsonc.JsonComment().load(config_file)


def summarize_important_emails(mail):
    if config.get("skip_summarization", False):
        logging.info("Summarization skipped as per configuration.")
        return

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
                    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)

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
        unread_msg_nums = response[0].split()

        for e_id in unread_msg_nums:
            _, msg_data = mail.fetch(e_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject = msg["Subject"]
                    body = get_email_body(msg)  # Function to extract the email body

                    # Tokenize the input
                    inputs = tokenizer(
                        body[: config.get("max_email_body_length", 512)],
                        return_tensors="pt",
                        max_length=config.get("max_email_body_length", 512),
                        truncation=True,
                    )

                    # Perform sentiment analysis (assuming you have a suitable classification model)
                    outputs = model(**inputs)
                    sentiment = outputs.logits.argmax(dim=1).item()

                    sentiment_labels = config.get(
                        "sentiment_labels", ["Negative", "Positive"]
                    )
                    logging.info(
                        f"Sentiment of email '{subject}': {sentiment_labels[sentiment]}"
                    )
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
                except Exception:
                    return part.get_payload(decode=True).decode(
                        "latin1", errors="replace"
                    )
    else:
        try:
            return msg.get_payload(decode=True).decode("utf-8", errors="replace")
        except Exception as e:
            return msg.get_payload(decode=True).decode("latin1", errors="replace")
    return ""
