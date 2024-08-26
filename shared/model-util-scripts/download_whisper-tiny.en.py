import torch
from transformers import WhisperForConditionalGeneration, BitsAndBytesConfig
import os
import logging
import shutil

# Set the directory path where you want to store the Whisper model
model_directory_path = "/home/ncacord/N.E.X.U.S.-Server/shared/models/whisper-tiny.en"

# Set up logging
log_file_path = "/home/ncacord/N.E.X.U.S.-Server/shared/logs/whisper_download.log"
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
logging.basicConfig(filename=log_file_path, level=logging.INFO)

# Configure the model for 8-bit quantization using bitsandbytes
quantization_config = BitsAndBytesConfig(
    load_in_8bit=True,
    llm_int8_threshold=6.0,
)

# Number of retries in case of failure
max_retries = 3


def calculate_directory_size(directory):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(directory):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size


def log_directory_size(directory):
    size_in_bytes = calculate_directory_size(directory)
    size_in_mb = size_in_bytes / (1024 * 1024)
    logging.info(f"Total model directory size: {size_in_mb:.2f} MB")


def save_model_with_retry(model, save_path, retries=0):
    try:
        model.save_pretrained(save_path)
        logging.info(f"Model successfully saved to '{save_path}'")
        log_directory_size(save_path)
    except Exception as e:
        if retries < max_retries:
            retries += 1
            logging.warning(f"Retrying save... Attempt {retries}/{max_retries}")
            save_model_with_retry(model, save_path, retries)
        else:
            logging.error(
                f"Failed to save model after {max_retries} attempts. Error: {str(e)}"
            )


try:
    # Load the model with quantization on the GPU
    model = WhisperForConditionalGeneration.from_pretrained(
        "openai/whisper-tiny.en",
        cache_dir=model_directory_path,
        quantization_config=quantization_config,
        device_map="auto",
    )
    logging.info("Model successfully loaded with 8-bit quantization.")

    # Save the quantized model with retry logic
    save_model_with_retry(model, model_directory_path)

except FileNotFoundError as e:
    os.makedirs(model_directory_path, exist_ok=True)
    logging.error(
        f"Model directory '{model_directory_path}' not found. Original exception: {str(e)}"
    )
    # Retry loading the model after creating the directory
    model = WhisperForConditionalGeneration.from_pretrained(
        "openai/whisper-tiny.en",
        cache_dir=model_directory_path,
        quantization_config=quantization_config,
        device_map="auto",
    )
    logging.info(
        "Model successfully loaded with 8-bit quantization after directory creation."
    )
    save_model_with_retry(model, model_directory_path)
except NotADirectoryError as e:
    logging.error(
        f"Model directory '{model_directory_path}' is not a valid directory. Original exception: {str(e)}"
    )
    # Handle the error by creating a new directory or notifying the user
    new_directory_path = model_directory_path + "_new"
    os.makedirs(new_directory_path, exist_ok=True)
    logging.info(f"Created a new directory '{new_directory_path}' to store the model.")
    model_directory_path = new_directory_path

    # Retry loading the model after creating the new directory
    model = WhisperForConditionalGeneration.from_pretrained(
        "openai/whisper-tiny.en",
        cache_dir=model_directory_path,
        quantization_config=quantization_config,
        device_map="auto",
    )
    logging.info(
        "Model successfully loaded with 8-bit quantization after new directory creation."
    )
    save_model_with_retry(model, model_directory_path)
except Exception as e:
    logging.exception(f"An error occurred: {str(e)}")
