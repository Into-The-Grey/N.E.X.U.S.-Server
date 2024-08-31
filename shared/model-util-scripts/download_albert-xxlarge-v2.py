from transformers import AutoModelForMaskedLM, AutoTokenizer
from pathlib import Path
import torch
import logging

# Set up logging
log_file = "/home/ncacord/N.E.X.U.S.-Server/shared/logs/download_albert-xxlarge-v2.log"
Path(log_file).parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=log_file,
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Set device to GPU if available, otherwise use CPU
device = torch.device("cuda:1" if torch.cuda.is_available() else "cpu")

# Define model directory and file names
model_path = Path("/home/ncacord/N.E.X.U.S.-Server/shared/models/albert-xxlarge-v2")

# Check if the necessary model files exist
required_files = ["config.json", "tokenizer_config.json"]
model_files_exist = all((model_path / file).exists() for file in required_files)

# Set torch_dtype to torch.float16 if the device type is "cuda", otherwise set it to None
torch_dtype = torch.float16 if device.type == "cuda" else None

# Load or download the model and tokenizer
if not model_files_exist:
    logging.info(f"Downloading model to {model_path}...")
    tokenizer = AutoTokenizer.from_pretrained("albert-xxlarge-v2", use_fast=True)
    model = AutoModelForMaskedLM.from_pretrained(
        "albert-xxlarge-v2", torch_dtype=torch_dtype
    )

    # Save the model and tokenizer directly to the model_path
    model.save_pretrained(model_path, safe_serialization=True)
    tokenizer.save_pretrained(model_path)
else:
    logging.info(f"Loading model from {model_path}...")
    tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=True)
    model = AutoModelForMaskedLM.from_pretrained(model_path, torch_dtype=torch_dtype)

# Move model to the specified device
model = model.to(device)

# Example sentence for masked language modeling
masked_sentence = "The capital of France is [MASK]."
inputs = tokenizer(masked_sentence, return_tensors="pt").to(device)

# Perform inference
try:
    outputs = model(**inputs)
except RuntimeError as e:
    if "out of memory" in str(e):
        # Handle CUDA out-of-memory error
        if device.type == "cuda":
            torch.cuda.empty_cache()
            inputs = {key: tensor.to("cpu") for key, tensor in inputs.items()}
            outputs = model(**inputs)
        else:
            raise e
    else:
        logging.error(str(e))
        raise e

# Confirm the model and tokenizer are stored in the appropriate directory
logging.info(f"Model and tokenizer are stored in {model_path}")
