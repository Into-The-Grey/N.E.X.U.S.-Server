from datetime import datetime, timedelta, timezone
import imaplib
import email
import logging
import json
import os


# Load configuration settings from the config.json file
with open(
    "/home/ncacord/N.E.X.U.S.-Server/cores/connectivity-core/email_management/config.json",
    "r",
) as config_file:
    config = json.load(config_file)

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
    except imaplib.IMAP4.error as e:
        logging.error(f"Failed to count unread emails: {str(e)}")
        return 0
    except Exception as e:
        logging.error(f"An error occurred while counting unread emails: {str(e)}")
        return 0


from concurrent.futures import ThreadPoolExecutor


def process_email(mail, e_id, sorting_rules, config):
    _, msg_data = mail.fetch(e_id, "(BODY[HEADER.FIELDS (SUBJECT FROM)])")
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
                        status, _ = mail.store(e_id, "+X-GM-LABELS", rule["label"])
                        if status == "OK":
                            if not config.get("sort_in_background", False):
                                logging.info(
                                    f"Labeled email from {from_} with subject '{subject}' as '{rule['label']}'"
                                )
                            if config.get("auto_archive_after_sort", False):
                                mail.store(e_id, "+FLAGS", "\\Archive")
                        else:
                            logging.error(
                                f"Failed to label email from {from_} with subject '{subject}' as '{rule['label']}'"
                            )
                        break


def automatically_sort_emails(mail, config):
    # Fetch all email headers at once
    _, all_msg_nums = mail.search(None, "ALL")
    all_msg_nums = all_msg_nums[0].split()[: min(config.get("max_emails_per_run", 100), len(all_msg_nums))]

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

    with ThreadPoolExecutor() as executor:
        futures = []
        for e_id in all_msg_nums:
            futures.append(
                executor.submit(process_email, mail, e_id, sorting_rules, config)
            )

        # Wait for all tasks to complete
        for future in futures:
            future.result()

    mail.expunge()
    logging.info("Finished sorting and labeling emails.")
    # Remove the redundant redefinition of sorting_rules

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
            search_criteria = f'(SINCE "{(datetime.now(timezone.utc) - timedelta(days=1)).strftime("%d-%b-%Y")}")'

        if config.get("only_sort_recent", False):
            # Only sort emails received within the last 24 hours
            search_criteria = f'(SINCE "{(datetime.now(timezone.utc) - timedelta(days=1)).strftime("%d-%b-%Y")}")'

        status, response = mail.search(None, search_criteria)
        if status == "OK":
            all_msg_nums = response[0].split()[: config.get("max_emails_per_run", 100)]
        else:
            logging.error("Failed to search for all emails.")
            return

        for e_id in all_msg_nums:
            _, msg_data = mail.fetch(e_id, "(BODY[HEADER.FIELDS (SUBJECT FROM)])")
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
                                        mail.store(e_id, "+FLAGS", "\\Archive")
                                else:
                                    logging.error(
                                        f"Failed to label email from {from_} with subject '{subject}' as '{rule['label']}'"
                                    )
                                break
        mail.expunge()
        logging.info("Finished sorting and labeling emails.")
    except Exception as e:
        logging.error(f"Failed to sort emails: {str(e)}")
