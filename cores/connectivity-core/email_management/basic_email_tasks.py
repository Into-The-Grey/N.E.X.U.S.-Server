import imaplib
import email
import logging


def count_unread_emails(mail):
    try:
        mail.select("inbox")
        status, response = mail.search(None, "UNSEEN")
        unread_msg_nums = response[0].split()
        logging.info(f"Unread emails count: {len(unread_msg_nums)}")
        return len(unread_msg_nums)
    except Exception as e:
        logging.error(f"Failed to count unread emails: {str(e)}")
        return 0


def automatically_sort_emails(mail, sorting_rules):
    try:
        mail.select("inbox")
        status, response = mail.search(None, "ALL")
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
                                # Move the email to the appropriate folder
                                mail.copy(e_id, rule["folder"])
                                mail.store(e_id, "+FLAGS", "\\Deleted")
                                logging.info(
                                    f"Moved email from {from_} with subject '{subject}' to folder '{rule['folder']}'"
                                )
                                break
        mail.expunge()  # Delete the moved emails from the inbox
    except Exception as e:
        logging.error(f"Failed to sort emails: {str(e)}")
