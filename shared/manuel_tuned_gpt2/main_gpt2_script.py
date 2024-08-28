import json
import logging
import argparse
import os
import sys
from transformers import pipeline
from management_scripts.context_manager import context_manager
from management_scripts.session_manager import session_manager
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    AutoModelForMaskedLM,
)
from response_filters.strict_format import strict_format
from management_scripts.feedback_manager import (
    collect_feedback,
)
from management_scripts.parameter_manager import (
    set_generation_parameter,
    get_generation_parameters,
    explain_generation_parameters,
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
if response_config_path is None:
    logging.error("Response config path not specified in environment variables.")
    exit(1)
sentiment_response_config_path = os.getenv("SENTIMENT_RESPONSE_CONFIG")
if sentiment_response_config_path is None:
    logging.error(
        "Sentiment response config path not specified in environment variables."
    )
    exit(1)

# Configure logging
logging_dir = os.getenv(
    "LOGGING_DIR", "/home/ncacord/N.E.X.U.S.-Server/shared/manuel_tuned_gpt2/logs"
)
log_file_name = "gpt2_sudo_tuned.log"  # Custom log file name for this script
log_file_path = os.path.join(logging_dir, log_file_name)


logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    force=True,
)

logging.info("Starting models...")


# Load GPT-2 model and tokenizer
def load_gpt2_model_and_tokenizer(gpt2_model_path):
    try:
        gpt2_model = AutoModelForCausalLM.from_pretrained(
            gpt2_model_path, local_files_only=True
        )
        gpt2_tokenizer = AutoTokenizer.from_pretrained(
            gpt2_model_path, local_files_only=True
        )
        logging.info(f"GPT-2 model and tokenizer loaded from {gpt2_model_path}.")
        return gpt2_model, gpt2_tokenizer
    except Exception as e:
        logging.error(f"Error loading GPT-2 model or tokenizer: {e}")
        exit(1)


if not gpt2_model_path:
    logging.error("GPT-2 model path not specified in environment variables.")
    exit(1)
elif gpt2_model_path is None or not os.path.exists(gpt2_model_path):
    logging.error(f"Invalid GPT-2 model path: {gpt2_model_path}")
    exit(1)

gpt2_model, gpt2_tokenizer = load_gpt2_model_and_tokenizer(gpt2_model_path)


# Load ALBERT model and tokenizer
def load_albert_model_and_tokenizer(albert_model_path):
    try:
        albert_model = AutoModelForMaskedLM.from_pretrained(
            albert_model_path, local_files_only=True
        )
        albert_tokenizer = AutoTokenizer.from_pretrained(
            albert_model_path, local_files_only=True
        )
        logging.info(f"ALBERT model and tokenizer loaded from {albert_model_path}.")
        return albert_model, albert_tokenizer
    except Exception as e:
        logging.error(f"Error loading ALBERT model or tokenizer: {e}")
        exit(1)


if not albert_model_path:
    logging.error("ALBERT model path not specified in environment variables.")
    exit(1)
elif albert_model_path is None or not os.path.exists(albert_model_path):
    logging.error(f"Invalid ALBERT model path: {albert_model_path}")
    exit(1)

try:
    albert_model = AutoModelForMaskedLM.from_pretrained(
        albert_model_path, local_files_only=True
    )
    albert_tokenizer = AutoTokenizer.from_pretrained(
        albert_model_path, local_files_only=True
    )
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


# Load the sentiment response config file
def load_sentiment_response_config(sentiment_response_config_path):
    if os.path.exists(sentiment_response_config_path):
        try:
            with open(sentiment_response_config_path, "r") as file:
                return json.load(file)
        except Exception as e:
            logging.error(f"Error loading sentiment response config file: {e}")
            exit(1)
    else:
        logging.error(
            f"Sentiment response config file not found at {sentiment_response_config_path}"
        )
        exit(1)


response_config = load_response_config(response_config_path)
sentiment_response_config = load_sentiment_response_config(
    sentiment_response_config_path
)


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


# Load sentiment analysis model with specified device
import torch

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
sentiment_analyzer = pipeline("sentiment-analysis", device=device)


def generate_response(prompt):
    try:
        logging.info(f"Processing prompt: {prompt}")

        # Analyze input with ALBERT before generating response with GPT-2
        analysis = analyze_input_with_albert(prompt)

        # Incorporate session context into the prompt
        contextual_prompt = session_manager.get_contextual_prompt(prompt)

        # Generate response with dynamic parameters
        params = get_generation_parameters()
        inputs = gpt2_tokenizer(contextual_prompt, return_tensors="pt")
        outputs = gpt2_model.generate(
            **inputs,
            max_length=params["max_length"],
            temperature=params["temperature"],
            top_k=params["top_k"],
            top_p=params["top_p"],
            do_sample=True,  # Enable sampling if using top_p or top_k
        )
        response = gpt2_tokenizer.decode(
            outputs[0], skip_special_tokens=True, clean_up_tokenization_spaces=True
        )
        logging.info(f"Generated response for prompt '{prompt}': {response}")

        # Add the interaction to the session memory
        session_manager.add_to_session(prompt, response)

        return apply_filters(response)
    except MemoryError:
        logging.error(
            "Memory error during response generation. Try reducing max_length or other parameters."
        )
        return "I'm sorry, there was a memory issue processing your request."
    except Exception as e:
        logging.error(f"Error generating response: {e}")
        return "I'm sorry, something went wrong with processing your request."


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "prompt", type=str, help="The prompt for generating a response."
    )
    parser.add_argument(
        "--set_param",
        nargs=2,
        metavar=("param_name", "value"),
        help="Set a generation parameter (e.g., --set_param temperature 0.8)",
    )
    parser.add_argument(
        "--explain_params",
        action="store_true",
        help="Explain the current generation parameters.",
    )
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Run the model in a loop to continuously process prompts.",
    )
    args = parser.parse_args()

    if args.set_param is not None:
        param_name, value = args.set_param
        try:
            value = float(value) if "." in value else int(value)
            set_generation_parameter(param_name, value)
            print(f"Set {param_name} to {value}.")
        except ValueError:
            print(
                f"Invalid value for {param_name}: {value}. Please provide a valid numeric value."
            )
        return

    if args.explain_params:
        explain_generation_parameters()
        return

    import asyncio

    if args.loop:
        print("Entering loop mode. Type 'exit' to stop.")
        loop = asyncio.get_event_loop()
        while True:
            try:
                prompt = await loop.run_in_executor(None, input, "Enter your prompt: ")
                if prompt.lower() == "exit":
                    break
                if not prompt.strip():
                    print("Input is empty. Please provide a valid prompt.")
                    continue
                response = await loop.run_in_executor(None, generate_response, prompt)
                logging.info(
                    f"Collected feedback for prompt '{prompt}' and response '{response}'."
                )
                print(response)
                await loop.run_in_executor(None, collect_feedback, prompt, response)
            except (EOFError, KeyboardInterrupt):
                print("\nExiting loop mode.")
                break
        return

    prompt = args.prompt.strip()
    if args.prompt is None:
        print("Input is empty. Please provide a valid prompt.")
        return
    prompt = args.prompt.strip()
    if not prompt:
        print("Input is empty. Please provide a valid prompt.")
        return

    response = generate_response(prompt)
    print(response)
    collect_feedback(prompt, response)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
