import os
from transformers import AutoTokenizer
from datasets import Dataset
from dotenv import load_dotenv

# Load environment variables (if necessary)
load_dotenv()

# Set the dataset name and file paths
dataset_name = "daily_dialog"
train_path = "/home/ncacord/N.E.X.U.S.-Server/shared/data/datasets/daily_dialog/dialogues_train.txt"
validation_path = "/home/ncacord/N.E.X.U.S.-Server/shared/data/datasets/daily_dialog/dialogues_validation.txt"
block_size = 128

# Initialize the tokenizer
tokenizer = AutoTokenizer.from_pretrained("gpt2")

# Load the dialogues from the text files into lists
with open(train_path, "r") as f:
    train_dialogues = f.readlines()

with open(validation_path, "r") as f:
    validation_dialogues = f.readlines()

# Convert the dialogues into datasets
train_dataset = Dataset.from_dict({"dialog": train_dialogues})
validation_dataset = Dataset.from_dict({"dialog": validation_dialogues})

datasets = {
    "train": train_dataset,
    "validation": validation_dataset,
}


# Tokenize the datasets
def tokenize_function(examples):
    # Ensure the tokenizer has a pad token
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    return tokenizer(
        examples["dialog"],
        truncation=True,
        padding="max_length",
        max_length=block_size,
    )


tokenized_datasets = {
    split: datasets[split].map(tokenize_function, batched=True) for split in datasets
}

# Save tokenized datasets to disk with the dynamic dataset name
save_path = (
    f"/home/ncacord/N.E.X.U.S.-Server/shared/data/tokenized_datasets/{dataset_name}"
)
os.makedirs(save_path, exist_ok=True)

for split in tokenized_datasets:
    tokenized_datasets[split].save_to_disk(f"{save_path}/{split}")

print(f"Tokenized datasets saved to {save_path}")
