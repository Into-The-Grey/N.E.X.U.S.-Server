import json
import logging
import os
from transformers import AutoModelForCausalLM, AutoTokenizer
from response_filters.strict_format import strict_format

# Load configuration
try:
    with open("config.json") as config_file:
        config = json.load(config_file)
except FileNotFoundError:
    print("Configuration file not found.")
    exit(1)
except json.JSONDecodeError:
    print("Error decoding the configuration file.")
    exit(1)

# Configure logging
log_file_path = "/home/ncacord/N.E.X.U.S.-Server/shared/manuel_tuned_gpt2/logs/gpt2_sudo_tuned.log"  # Replace with your desired log file path
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
logging.basicConfig(filename=log_file_path, level=logging.INFO)

# Load model and tokenizer
model_path = config.get("model_path")
if not model_path:
    print("Model path not specified in the configuration.")
    exit(1)
model = AutoModelForCausalLM.from_pretrained(model_path)
tokenizer = AutoTokenizer.from_pretrained(model_path)


def apply_filters(response):
    if (
        config.get("response_filters", {})
        .get("strict_format", {})
        .get("enabled", False)
    ):
        response = strict_format(
            response, config["response_filters"]["strict_format"]["variations"]
        )
    # Apply other filters as necessary
    return response


def generate_response(prompt):
    inputs = tokenizer(prompt, return_tensors="pt")
    outputs = model.generate(**inputs)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return apply_filters(response)


if __name__ == "__main__":
    prompt = "Your input prompt here"
    try:
        response = generate_response(prompt)
        print(response)
        logging.info(f"Generated response: {response}")
    except Exception as e:
        print(f"An error occurred during response generation: {e}")
        logging.error(f"Error occurred: {e}")
