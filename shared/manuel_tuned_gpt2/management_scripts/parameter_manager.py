import logging
import os
import csv
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(
    dotenv_path="/home/ncacord/N.E.X.U.S.-Server/shared/manuel_tuned_gpt2/chatbot.env",
    verbose=True,
    override=True,
)

# Configure logging
logging_dir = os.environ.get(
    "LOGGING_DIR", "/home/ncacord/N.E.X.U.S.-Server/shared/manual_tuned_gpt2/logs"
)
log_file_name = "param_manager.log"  # Set the name of the log file here
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

# Define the adjustable parameters with default values
generation_parameters = {
    "temperature": 1.0,  # Controls randomness; higher values = more random
    "top_k": 50,  # Limits sampling to top-k logits; lower values = more focused
    "top_p": 0.9,  # Limits sampling to a cumulative probability; similar to top_k
    "max_length": 50,  # Maximum length of the generated sequence
}

feedback_file = "/home/ncacord/N.E.X.U.S.-Server/shared/manual_tuned_gpt2/feedback/interaction_data.csv"


def set_generation_parameter(param_name, value):
    if param_name in generation_parameters:
        generation_parameters[param_name] = value
        logging.info(f"Set {param_name} to {value}")
    else:
        logging.error(f"Invalid parameter name: {param_name}")


def get_generation_parameters():
    return generation_parameters


def explain_generation_parameters():
    explanations = {
        "temperature": "Controls randomness in the response. Higher values make the output more random.",
        "top_k": "Limits the possible choices to the top K most likely next words. Lower values make the response more focused.",
        "top_p": "Limits the possible choices based on cumulative probability, making the output more predictable.",
        "max_length": "Sets the maximum length of the generated response.",
    }

    for param, value in generation_parameters.items():
        print(
            f"{param} ({value}): {explanations.get(param, 'No explanation available')}"
        )


def calculate_average_feedback(feedback_file, recent_count=10):
    """Calculate the average feedback from the last 'recent_count' interactions."""
    ratings = []
    try:
        with open(feedback_file, "r") as file:
            reader = csv.reader(file)
            for row in reader:
                if len(ratings) >= recent_count:
                    break
                ratings.append(int(row[2]))
    except Exception as e:
        logging.error(f"Error reading feedback file: {e}")

    if ratings:
        average_feedback = sum(ratings) / len(ratings)
        logging.info(f"Average feedback score: {average_feedback}")
        return average_feedback
    else:
        logging.warning("No feedback ratings found.")
        return None


def adjust_parameters_based_on_feedback(avg_feedback):
    """Adjust generation parameters if feedback score drops below threshold."""
    if avg_feedback is not None and avg_feedback < 7:
        set_generation_parameter(
            "temperature", max(0.5, generation_parameters["temperature"] - 0.1)
        )
        set_generation_parameter(
            "max_length", min(70, generation_parameters["max_length"] + 10)
        )
        logging.info("Parameters adjusted based on feedback.")
