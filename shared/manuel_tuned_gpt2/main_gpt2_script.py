import json
import logging
import argparse
import os
import sys
from transformers import (
    pipeline,
    AutoModelForCausalLM,
    AutoTokenizer,
    AutoModelForMaskedLM,
    AutoModelForSequenceClassification,
)
from management_scripts.context_manager import context_manager
from management_scripts.session_manager import session_manager
from response_filters.strict_format import strict_format
from management_scripts.feedback_manager import collect_feedback
from management_scripts.parameter_manager import (
    set_generation_parameter,
    get_generation_parameters,
    explain_generation_parameters,
)
from dotenv import load_dotenv
import torch
import asyncio

# Set up logging
logging.getLogger("transformers.modeling_utils").setLevel(logging.ERROR)
logging_dir = os.getenv(
    "LOGGING_DIR", "/home/ncacord/N.E.X.U.S.-Server/shared/manuel_tuned_gpt2/logs"
)
log_file_name = "gpt2_sudo_tuned.log"
log_file_path = os.path.join(logging_dir, log_file_name)
os.makedirs(logging_dir, exist_ok=True)
logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    force=True,
)

# Load environment variables
load_dotenv(
    dotenv_path="/home/ncacord/N.E.X.U.S.-Server/shared/manuel_tuned_gpt2/chatbot.env",
    verbose=True,
    override=True,
)

# Load paths from .env file
gpt2_model_path = os.getenv("GPT_MODEL_PATH")
albert_model_path = os.getenv("ALBERT_MODEL_PATH")
response_config_path = os.getenv("RESPONSE_CONFIG")
sentiment_response_config_path = os.getenv("SENTIMENT_RESPONSE_CONFIG")

# Check paths
if not all(
    [
        gpt2_model_path,
        albert_model_path,
        response_config_path,
        sentiment_response_config_path,
    ]
):
    logging.error("One or more necessary environment variables are not set.")
    sys.exit(1)

# Device selection
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
torch_dtype = torch.float16 if device.type == "cuda" else None


# Load GPT-2 model and tokenizer
def load_gpt2_model_and_tokenizer(model_path, torch_dtype=None):
    try:
        torch_dtype = torch_dtype or torch.float32  # Define torch_dtype if not provided
        model = AutoModelForCausalLM.from_pretrained(
            model_path, local_files_only=True, torch_dtype=torch_dtype
        )
        tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=True)
        logging.info(f"GPT-2 model and tokenizer loaded from {model_path}.")
        return model, tokenizer
    except Exception as e:
        logging.error(f"Error loading GPT-2 model or tokenizer: {e}")
        sys.exit(1)


gpt2_model, gpt2_tokenizer = load_gpt2_model_and_tokenizer(gpt2_model_path)


# Load ALBERT model and tokenizer
def load_albert_model_and_tokenizer(model_path):
    try:
        model = AutoModelForMaskedLM.from_pretrained(
            model_path,
            local_files_only=True,
            torch_dtype=torch_dtype,
        )
        tokenizer = AutoTokenizer.from_pretrained(
            model_path, local_files_only=True, use_fast=True
        )
        model.to(device)
        logging.info(f"ALBERT model and tokenizer loaded from {model_path}.")
        return model, tokenizer
    except Exception as e:
        logging.error(f"Error loading ALBERT model or tokenizer: {e}")
        sys.exit(1)


albert_model, albert_tokenizer = load_albert_model_and_tokenizer(albert_model_path)


# Load configuration files
def load_json_config(path):
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception as e:
        logging.error(f"Error loading config file {path}: {e}")
        sys.exit(1)


response_config = load_json_config(response_config_path)
sentiment_response_config = load_json_config(sentiment_response_config_path)


# Sentiment analysis pipeline
def load_sentiment_analyzer(model_path):
    try:
        sentiment_model = AutoModelForSequenceClassification.from_pretrained(
            model_path, local_files_only=True, torch_dtype=torch_dtype
        )
        sentiment_tokenizer = AutoTokenizer.from_pretrained(
            model_path, local_files_only=True, use_fast=True
        )
        analyzer = pipeline(
            "sentiment-analysis",
            model=sentiment_model,
            tokenizer=sentiment_tokenizer,
            device=device,
            torch_dtype=torch_dtype,
        )
        return analyzer
    except Exception as e:
        logging.error(f"Error loading sentiment analysis model: {e}")
        sys.exit(1)


sentiment_analyzer = load_sentiment_analyzer(albert_model_path)


# Analyze input with ALBERT
def analyze_input_with_albert(prompt):
    try:
        inputs = albert_tokenizer(prompt, return_tensors="pt")
        albert_model(**inputs.to(device))
        sentiment = "neutral"  # Placeholder sentiment detection logic
        logging.info(f"Detected sentiment: {sentiment}")
        return
    except Exception as e:
        logging.error(f"Error analyzing input with ALBERT: {e}")
        return None


# Apply response filters
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


# Generate response
def generate_response(prompt):
    logging.info(f"Processing prompt: {prompt}")
    analysis = analyze_input_with_albert(prompt)
    contextual_prompt = session_manager.get_contextual_prompt(prompt)
    params = get_generation_parameters()
    with torch.no_grad():
        inputs = gpt2_tokenizer(contextual_prompt, return_tensors="pt").to(device)
        outputs = gpt2_model.generate(
            **inputs,
            max_length=params["max_length"],
            temperature=params["temperature"],
            top_k=params["top_k"],
            top_p=params["top_p"],
            do_sample=True,
        )
    response = gpt2_tokenizer.decode(
        outputs[0], skip_special_tokens=True, clean_up_tokenization_spaces=True
    )
    logging.info(f"Generated response for prompt '{prompt}': {response}")
    session_manager.add_to_session(prompt, response)
    return apply_filters(response)


# Main function
async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "prompt",
        type=str,
        nargs="?",
        default="",
        help="The prompt for generating a response.",
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

    if args.set_param:
        param_name, value = args.set_param
        if param_name not in get_generation_parameters():
            print(
                f"Invalid parameter name: {param_name}. Please provide a valid parameter name."
            )
            return
        try:
            value = float(value) if "." in value else int(value)
        except ValueError:
            print(
                f"Invalid value for {param_name}: {value}. Please provide a valid numeric value."
            )
            return

        set_generation_parameter(param_name, value)
        print(f"Set {param_name} to {value}.")
        return

    if args.explain_params:
        explain_generation_parameters()
        return

    if args.loop:
        loop = asyncio.get_event_loop()
        print("Entering loop mode. Type 'exit' to stop.")
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
            except Exception as e:
                logging.error(f"An error occurred in loop mode: {e}")
                print(f"An error occurred: {e}")
                break
        return

    prompt = args.prompt.strip()
    if not prompt:
        print("Input is empty. Please provide a valid prompt.")
        return

    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, generate_response, prompt)
        print(response)
        collect_feedback(prompt, response)
    except Exception as e:
        logging.error(f"An error occurred during response generation: {e}")
        print("An error occurred during response generation.")


if __name__ == "__main__":
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("\nChat session terminated by user.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        if loop is not None:
            loop.close()
        print("Cleanup complete. Exiting.")
