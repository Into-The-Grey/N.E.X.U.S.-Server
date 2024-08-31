import datetime
from datetime import timedelta
import imaplib
import email
import logging
import json
import jsoncomment as jsonc

# Load configuration settings from the config.jsonc file
with open(
    "/home/ncacord/N.E.X.U.S.-Server/cores/connectivity-core/email_management/config.jsonc",
    "r",
) as config_file:
    config = jsonc.JsonComment().load(config_file)

# Setup logging based on the config settings
log_level = getattr(logging, config.get("log_level", "INFO").upper(), logging.INFO)
logging.basicConfig(
    filename="/home/ncacord/N.E.X.U.S.-Server/cores/connectivity-core/logs/email_management.log",
    level=log_level,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def count_unread_emails(mail):
    try:
        status, _ = mail.select("inbox")
        if status == "OK":
            logging.info("Inbox selected successfully.")
        else:
            logging.error("Failed to select inbox.")
            return 0
        status, response = mail.search(None, "UNSEEN")
        if status == "OK":
            unread_msg_nums = response[0].split()
            logging.info(f"Unread emails count: {len(unread_msg_nums)}")
            return len(unread_msg_nums)
        else:
            logging.error("Failed to search for unread emails.")
            return 0
    except Exception as e:
        logging.error(f"Failed to count unread emails: {str(e)}")
        return 0


def automatically_sort_emails(mail, config):
    # Load custom sorting rules or use the defaults
    sorting_rules = config.get(
        "custom_sorting_rules",
        [
            {
                "condition": lambda subject, from_: "invoice" in subject.lower(),
                "label": "Invoices",
            },
            {
                "condition": lambda subject, from_: "newsletter" in subject.lower(),
                "label": "Newsletters",
            },
            {
                "condition": lambda subject, from_: "order confirmation"
                in subject.lower()
                or "purchase" in subject.lower(),
                "label": "Shopping",
            },
            {
                "condition": lambda subject, from_: "shipment" in subject.lower()
                or "tracking" in subject.lower(),
                "label": "Shipping",
            },
            {
                "condition": lambda subject, from_: "game" in subject.lower()
                or "gaming" in subject.lower(),
                "label": "Gaming",
            },
            {
                "condition": lambda subject, from_: "sale" in subject.lower()
                or "discount" in subject.lower(),
                "label": "Promotions",
            },
            {
                "condition": lambda subject, from_: "subscription" in subject.lower()
                or "renewal" in subject.lower(),
                "label": "Subscriptions",
            },
            {
                "condition": lambda subject, from_: "support" in subject.lower()
                or "help" in subject.lower(),
                "label": "Support",
            },
            {
                "condition": lambda subject, from_: "social" in subject.lower()
                or "friend request" in subject.lower(),
                "label": "Social",
            },
            {
                "condition": lambda subject, from_: "security alert" in subject.lower()
                or "password reset" in subject.lower(),
                "label": "Security",
            },
        ],
    )

    try:
        status, _ = mail.select("inbox")
        if status == "OK":
            logging.info("Inbox selected successfully.")
        else:
            logging.error("Failed to select inbox.")
            return

        search_criteria = "ALL"
        if not config.get("rescan_all", False):
            # Skip emails that already have one of the labels
            label_conditions = " ".join(
                [f'"{rule["label"]}"' for rule in sorting_rules]
            )
            search_criteria = f"ALL NOT X-GM-LABELS {label_conditions}"

        if config.get("only_sort_recent", False):
            # Only sort emails received within the last 24 hours
            search_criteria = f'(SINCE "{(datetime.datetime.now() - timedelta(days=1)).strftime("%d-%b-%Y")}")'

        status, response = mail.search(None, search_criteria)
        if status == "OK":
            all_msg_nums = response[0].split()[: config.get("max_emails_per_run", 100)]
        else:
            logging.error("Failed to search for all emails.")
            return

        for e_id in all_msg_nums:
            _, msg_data = mail.fetch(e_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject = msg["Subject"]
                    from_ = msg.get("From")

                    if subject and from_:
                        subject_lower = subject.lower()
                        from_lower = from_.lower()
                        for rule in sorting_rules:
                            if rule["condition"](subject_lower, from_lower):
                                status, _ = mail.store(
                                    e_id, "+X-GM-LABELS", rule["label"]
                                )
                                if status == "OK":
                                    if not config.get("sort_in_background", False):
                                        logging.info(
                                            f"Labeled email from {from_} with subject '{subject}' as '{rule['label']}'"
                                        )
                                    if config.get("auto_archive_after_sort", False):
                                        mail.store(e_id, "+FLAGS", "\\Archived")
                                else:
                                    logging.error(
                                        f"Failed to label email from {from_} with subject '{subject}' as '{rule['label']}'"
                                    )
                                break
        mail.expunge()
        logging.info("Finished sorting and labeling emails.")
    except Exception as e:
        logging.error(f"Failed to sort emails: {str(e)}")
