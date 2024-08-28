from transformers import AutoModelForMaskedLM, AutoTokenizer
from transformers import AutoConfig
from pathlib import Path
import torch
import logging

logging.getLogger("transformers.modeling_utils").setLevel(logging.ERROR)

# Set device to GPU 1 if available, otherwise use CPU
device = torch.device("cuda:1" if torch.cuda.is_available() else "cpu")

# Define model directory and file names
model_path = Path("/home/ncacord/N.E.X.U.S.-Server/shared/models/albert-xxlarge-v2")

# Check if the necessary model files exist
required_files = ["config.json", "pytorch_model.bin", "tokenizer_config.json", "vocab.txt"]
model_files_exist = all((model_path / file).exists() for file in required_files)

# Set the torch_dtype based on the device type
# If the device type is "cuda", set torch_dtype to torch.float16
# Otherwise, set torch_dtype to None
torch_dtype = torch.float16 if device.type == "cuda" else None

# Load or download the model and tokenizer
if not model_files_exist:
    print(f"Downloading model to {model_path}...")
    tokenizer = AutoTokenizer.from_pretrained("albert-xxlarge-v2", use_fast=True)
    model = AutoModelForMaskedLM.from_pretrained(
        "albert-xxlarge-v2", torch_dtype=torch.float16
    )

    # Save the model and tokenizer directly to the model_path
    model.save_pretrained(model_path, safe_serialization=True)
    tokenizer.save_pretrained(model_path)
else:
    print(f"Loading model from {model_path}...")
    tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=True)
    model = AutoModelForMaskedLM.from_pretrained(model_path, torch_dtype=torch_dtype)

# Move model to the specified device
model.to(device)

# Example sentence for masked language modeling
masked_sentence = "The capital of France is [MASK]."
inputs = tokenizer(masked_sentence, return_tensors="pt").to(device)

# Perform inference
try:
    outputs = model(**inputs)
except RuntimeError as e:
    if "out of memory" in str(e):
        # Handle CUDA out-of-memory error
        torch.cuda.empty_cache()
        model.to("cpu")
        inputs = {key: tensor.to("cpu") for key, tensor in inputs.items()}
        outputs = model(**inputs)
    else:
        raise e

# Confirm the model and tokenizer are stored in the appropriate directory
print(f"Model and tokenizer are stored in {model_path}")
