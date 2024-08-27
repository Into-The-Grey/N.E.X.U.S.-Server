import csv
import os
import logging
from dotenv import load_dotenv

load_dotenv(
    dotenv_path="/home/ncacord/N.E.X.U.S.-Server/shared/manuel_tuned_gpt2/chatbot.env",
    verbose=True,
    override=True,
)

# Paths for storing session data
context_file = "/home/ncacord/N.E.X.U.S.-Server/shared/manuel_tuned_gpt2/model_context_memory/context_data.csv"
session_file = "/home/ncacord/N.E.X.U.S.-Server/shared/manuel_tuned_gpt2/model_context_memory/session_data.csv"
# Configure logging
logging_dir = os.environ.get(
    "LOGGING_DIR", "/home/ncacord/N.E.X.U.S.-Server/shared/manual_tuned_gpt2/logs"
)
log_file_name = "session_manager.log"  # Custom log file name for this script
log_file_path = os.path.join(logging_dir, log_file_name)

# Create the directory for the log file if it doesn't exist
if not os.path.exists(os.path.dirname(log_file_path)):
    os.makedirs(
        os.path.dirname(log_file_path), exist_ok=True
    )  # Ensure directory creation with exist_ok=True

logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
)


class SessionManager:
    """Manages session-based memory for tracking and utilizing user interactions."""

    def __init__(self):
        self.session_memory = []
        self.load_session_memory()

    def load_session_memory(self):
        """Loads session memory from a file, if it exists."""
        if os.path.exists(session_file):
            with open(session_file, "r") as file:
                reader = csv.reader(file)
                self.session_memory = [row for row in reader]

    def save_session_memory(self):
        """Saves the current session memory to a file."""
        with open(session_file, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerows(self.session_memory)

    def add_to_session(self, prompt, response):
        """Adds a new interaction to the session memory."""
        self.session_memory.append([prompt, response])
        if (
            len(self.session_memory) > 10
        ):  # Limit session memory to last 10 interactions
            self.session_memory.pop(0)
        self.save_session_memory()

        # Log the interaction
        logging.info(f"New interaction: Prompt='{prompt}', Response='{response}'")

    def get_contextual_prompt(self, prompt):
        """Creates a contextual prompt based on the session memory."""
        context = " ".join([f"User: {p} Bot: {r}" for p, r in self.session_memory])
        return f"{context} User: {prompt}"


session_manager = SessionManager()
