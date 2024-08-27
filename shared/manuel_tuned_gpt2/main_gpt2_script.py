import json
import logging
import argparse
import os
import sys
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    AutoModelForMaskedLM,
)
from response_filters.strict_format import strict_format
from feedback_collector import collect_feedback
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
log_file_name = "gpt2_sudo_tuned.log"  # Set the name of the log file here
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

logging.info("Starting models...")


# Load GPT-2 model and tokenizer
def load_gpt2_model_and_tokenizer(gpt2_model_path):
    try:
        gpt2_model = AutoModelForCausalLM.from_pretrained(gpt2_model_path)
        gpt2_tokenizer = AutoTokenizer.from_pretrained(gpt2_model_path)
        logging.info(f"GPT-2 model and tokenizer loaded from {gpt2_model_path}.")
        return gpt2_model, gpt2_tokenizer
    except Exception as e:
        logging.error(f"Error loading GPT-2 model or tokenizer: {e}")
        exit(1)


gpt2_model_path = os.environ.get("GPT_MODEL_PATH")
if not gpt2_model_path:
    logging.error("GPT-2 model path not specified in environment variables.")
    exit(1)
elif not os.path.exists(gpt2_model_path):
    logging.error(f"Invalid GPT-2 model path: {gpt2_model_path}")
    exit(1)

gpt2_model, gpt2_tokenizer = load_gpt2_model_and_tokenizer(gpt2_model_path)

# Load ALBERT model and tokenizer
albert_model_path = os.environ.get("ALBERT_MODEL_PATH")
if not albert_model_path:
    logging.error("ALBERT model path not specified in environment variables.")
    exit(1)
elif not os.path.exists(albert_model_path):
    logging.error(f"Invalid ALBERT model path: {albert_model_path}")
    exit(1)

try:
    albert_model = AutoModelForMaskedLM.from_pretrained(albert_model_path)
    albert_tokenizer = AutoTokenizer.from_pretrained(albert_model_path)
    logging.info(f"ALBERT model and tokenizer loaded from {albert_model_path}.")
except Exception as e:
    logging.error(f"Error loading ALBERT model or tokenizer: {e}")
    exit(1)


def analyze_input_with_albert(prompt):
    try:
        inputs = albert_tokenizer(prompt, return_tensors="pt")
        outputs = albert_model(**inputs)
        logging.info(f"ALBERT output: {outputs}")

        # Placeholder for sentiment or intent analysis
        sentiment = "neutral"  # Placeholder sentiment detection logic
        logging.info(f"Detected sentiment: {sentiment}")
        return outputs
    except Exception as e:
        logging.error(f"Error analyzing input with ALBERT: {e}")
        return None


def apply_filters(response):
    try:
        config = {
            "response_filters": {
                "strict_format": {
                    "enabled": True,
                    "variations": ["variation1", "variation2"],
                }
            }
        }  # Define the config variable with the necessary values
        if (
            config.get("response_filters", {})
            .get("strict_format", {})
            .get("enabled", False)
        ):
            response = strict_format(
                response, config["response_filters"]["strict_format"]["variations"]
            )
        return response
    except Exception as e:
        logging.error(f"Error applying filters: {e}")
        return response


def generate_response(prompt):
    try:
        logging.info(f"Processing prompt: {prompt}")

        # Analyze input with ALBERT before generating response with GPT-2
        analysis = analyze_input_with_albert(prompt)

        # Here you could modify the prompt based on ALBERT's analysis (e.g., detected sentiment)

        inputs = gpt2_tokenizer(prompt, return_tensors="pt")
        outputs = gpt2_model.generate(**inputs)
        response = gpt2_tokenizer.decode(outputs[0], skip_special_tokens=True)
        logging.info(f"Generated response for prompt '{prompt}': {response}")
        return apply_filters(response)
    except Exception as e:
        logging.error(f"Error generating response: {e}")
        return "I'm sorry, something went wrong with processing your request."


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "prompt", type=str, help="The prompt for generating a response."
    )
    args = parser.parse_args()

    prompt = args.prompt.strip()
    if not prompt:
        print("Input is empty. Please provide a valid prompt.")
        return

    response = generate_response(prompt)
    print(response)
    collect_feedback(prompt, response)


if __name__ == "__main__":
    main()
