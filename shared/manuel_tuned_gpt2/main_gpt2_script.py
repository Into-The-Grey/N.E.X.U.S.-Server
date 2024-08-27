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
from shared.manuel_tuned_gpt2.management_scripts.feedback_manager import (
    collect_feedback,
)
from shared.manuel_tuned_gpt2.management_scripts.parameter_manager import (
    set_generation_parameter,
    get_generation_parameters,
    explain_generation_parameters,
)
from shared.manuel_tuned_gpt2.management_scripts.nca_personal_info_manager import (
    get_personal_detail,
)
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(
    dotenv_path="/home/ncacord/N.E.X.U.S.-Server/shared/manuel_tuned_gpt2/chatbot.env",
    verbose=True,
    override=True,
)

# Load paths from the .env file
gpt2_model_path = os.getenv("GPT_MODEL_PATH")
albert_model_path = os.getenv("ALBERT_MODEL_PATH")
response_config_path = os.getenv("RESPONSE_CONFIG")

# Configure logging
logging_dir = os.environ.get(
    "LOGGING_DIR", "/home/ncacord/N.E.X.U.S.-Server/shared/manual_tuned_gpt2/logs"
)
log_file_name = "gpt2_sudo_tuned.log"  # Custom log file name for this script
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


if not gpt2_model_path:
    logging.error("GPT-2 model path not specified in environment variables.")
    exit(1)
elif not os.path.exists(gpt2_model_path):
    logging.error(f"Invalid GPT-2 model path: {gpt2_model_path}")
    exit(1)

gpt2_model, gpt2_tokenizer = load_gpt2_model_and_tokenizer(gpt2_model_path)

# Load ALBERT model and tokenizer
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


# Load the response config file
def load_response_config(response_config_path):
    if os.path.exists(response_config_path):
        try:
            with open(response_config_path, "r") as file:
                return json.load(file)
        except Exception as e:
            logging.error(f"Error loading response config file: {e}")
            exit(1)
    else:
        logging.error(f"Response config file not found at {response_config_path}")
        exit(1)


response_config = load_response_config(response_config_path)


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
        if (
            response_config.get("response_filters", {})
            .get("strict_format", {})
            .get("enabled", False)
        ):
            response = strict_format(
                response,
                response_config["response_filters"]["strict_format"]["variations"],
            )
        return response
    except Exception as e:
        logging.error(f"Error applying filters: {e}")
        return response


def generate_response(prompt):
    try:
        logging.info(f"Processing prompt: {prompt}")

        # Replace placeholders in the prompt with personal details
        prompt = prompt.replace("{last_name}", get_personal_detail("last_name"))
        prompt = prompt.replace("{first_name}", get_personal_detail("first_name"))
        prompt = prompt.replace("{birthday}", get_personal_detail("birthday"))
        prompt = prompt.replace("{address}", get_personal_detail("address"))

        # Analyze input with ALBERT before generating response with GPT-2
        analysis = analyze_input_with_albert(prompt)

        # Generate response with dynamic parameters
        params = get_generation_parameters()
        inputs = gpt2_tokenizer(prompt, return_tensors="pt")
        outputs = gpt2_model.generate(
            **inputs,
            max_length=params["max_length"],
            temperature=params["temperature"],
            top_k=params["top_k"],
            top_p=params["top_p"],
        )
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
