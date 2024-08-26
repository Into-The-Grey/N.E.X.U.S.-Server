import os
from datasets import load_dataset, DatasetDict
from transformers import AutoTokenizer
from dotenv import load_dotenv

# Load environment variables (if necessary)
load_dotenv()

# Set the dataset path
dataset_path = "Isotonic/human_assistant_conversation"

# Extract the dataset name from the path
dataset_name = dataset_path.split("/")[-1]

# Set the block size
block_size = 128

# Initialize the tokenizer
tokenizer = AutoTokenizer.from_pretrained("gpt2")

# Load the dataset with training and validation splits
datasets = DatasetDict(
    {
        "train": load_dataset(dataset_path, split="train[:90%]"),
        "validation": load_dataset(dataset_path, split="train[90%:]"),
    }
)


# Tokenize the datasets
def tokenize_function(examples):
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    return tokenizer(
        examples["text"],  # Adjust the key to match the new dataset
        truncation=True,
        padding="max_length",
        max_length=block_size,
    )


tokenized_datasets = datasets.map(tokenize_function, batched=True)

# Save tokenized datasets to disk with the dynamic dataset name
save_path = (
    f"/home/ncacord/N.E.X.U.S.-Server/shared/data/tokenized_datasets/{dataset_name}"
)
tokenized_datasets.save_to_disk(save_path)

print(f"Tokenized dataset saved to {save_path}")
