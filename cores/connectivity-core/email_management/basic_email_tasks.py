from datetime import datetime, timedelta, timezone
import imaplib
import email
import logging
import json
import os

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


def process_email(mail, e_id, sorting_rules, config):
    try:
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
    except Exception as e:
        logging.error(f"An error occurred while processing email: {str(e)}")


def automatically_sort_emails(mail, config):
    try:
        # Fetch all email headers at once
        _, all_msg_nums = mail.search(None, "ALL")
        all_msg_nums = all_msg_nums[0].split()
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
                    "label": "social",
                },
                {
                    "condition": lambda subject, from_: "security alert" in subject.lower()
                    or "password reset" in subject.lower(),
                    "label": "Security",
                },
            ],
        )

        if not config.get("rescan_all", False) and not config.get("only_sort_recent", False):
            # Skip emails that already have one of the labels
            label_conditions = " ".join(
                [f'"{rule["label"]}"' for rule in sorting_rules]
            )
            search_criteria = f"ALL NOT X-GM-LABELS {label_conditions}"
        elif config.get("only_sort_recent", False):
            # Only sort emails received within the last 24 hours
            search_criteria = f'(SINCE "{(datetime.now(timezone.utc) - timedelta(days=1)).strftime("%d-%b-%Y")}")'
        else:
            search_criteria = "ALL"

        try:
            status, response = mail.search(None, search_criteria)
            if status == "OK":
                all_msg_nums = response[0].split()[: config.get("max_emails_per_run", 100)]
            else:
                logging.error("Failed to search for all emails.")
                return
        except Exception as e:
            logging.error(f"An error occurred while searching for emails: {str(e)}")
            return

        for e_id in all_msg_nums:
            process_email(mail, e_id, sorting_rules, config)

        try:
            mail.expunge()
        except Exception as e:
            logging.error(f"An error occurred while expunging emails: {str(e)}")
        
        logging.info("Finished sorting and labeling emails.")
    except Exception as e:
        logging.error(f"Failed to sort emails: {str(e)}")
