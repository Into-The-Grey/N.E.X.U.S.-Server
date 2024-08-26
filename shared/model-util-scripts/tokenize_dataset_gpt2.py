import os
import pandas as pd
from transformers import AutoTokenizer
from datasets import Dataset, DatasetDict
from dotenv import load_dotenv

# Load environment variables (if necessary)
load_dotenv()

# Set the dataset name
dataset_name = "human_assistant_conversation"
# Set the block size
block_size = 128

# Initialize the tokenizer
tokenizer = AutoTokenizer.from_pretrained("gpt2")

# Load the CSV files
train_csv_path = "/home/ncacord/N.E.X.U.S.-Server/shared/data/datasets/human_assistant_conversation/train.csv"
test_csv_path = "/home/ncacord/N.E.X.U.S.-Server/shared/data/datasets/human_assistant_conversation/test.csv"

train_df = pd.read_csv(train_csv_path)
test_df = pd.read_csv(test_csv_path)

# Create Hugging Face datasets from the DataFrames
train_dataset = Dataset.from_pandas(train_df)
test_dataset = Dataset.from_pandas(test_df)

# Combine into a DatasetDict
datasets = DatasetDict({"train": train_dataset, "validation": test_dataset})


# Tokenize the datasets
def tokenize_function(examples):
    # Ensure the tokenizer has a pad token
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    return tokenizer(
        examples["prompt"] + examples["response"],
        truncation=True,
        padding="max_length",
        max_length=block_size,
        clean_up_tokenization_spaces=True,
    )


tokenized_datasets = datasets.map(tokenize_function, batched=True)

# Save tokenized datasets to disk with the dynamic dataset name
save_path = (
    f"/home/ncacord/N.E.X.U.S.-Server/shared/data/tokenized_datasets/{dataset_name}"
)
tokenized_datasets.save_to_disk(save_path)

print(f"Tokenized dataset saved to {save_path}")
