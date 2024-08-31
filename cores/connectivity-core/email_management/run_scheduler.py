import os
import schedule
import time
import logging

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


def run_email_management():
    try:
        # Run the email_management.py script
        os.system(
            "python3 /home/ncacord/N.E.X.U.S.-Server/cores/connectivity-core/email_management.py"
        )
        logging.info("Ran email_management.py successfully.")
    except Exception as e:
        logging.error(f"Failed to run email_management.py: {str(e)}")


# Schedule the tasks to run at 12am, 6am, 12pm, and 6pm
# schedule.every().day.at("00:00").do(run_email_management)
# schedule.every().day.at("06:00").do(run_email_management)
# schedule.every().day.at("12:00").do(run_email_management)
# schedule.every().day.at("18:00").do(run_email_management)

# Keep the script running
# while True:
#     schedule.run_pending()
#     time.sleep(1)
