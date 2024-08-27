import logging
import os
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
