import logging
from transformers import AutoTokenizer
from datasets import load_dataset, DatasetDict
from dotenv import load_dotenv
from tqdm import tqdm

# Load environment variables (if necessary)
load_dotenv()

# Set up logging for telemetry
logging.basicConfig(
    filename="/home/ncacord/N.E.X.U.S.-Server/shared/logs/nexus_telemetry.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Set the dataset URL
dataset_url = "OpenAssistant/oasst1"

# Automatically set the dataset name based on the URL
dataset_name = dataset_url.split("/")[-1]

# Set the block size
block_size = 128  # You can try increasing this if needed, but be cautious.

try:
    # Initialize the tokenizer
    tokenizer = AutoTokenizer.from_pretrained("gpt2")

    # Load the dataset from Hugging Face using the dynamic URL
    logging.info(f"Loading dataset from URL: {dataset_url}")
    ds = load_dataset(dataset_url)  # Using 'ds' as specified

    # Load individual splits based on available split names
    train_dataset = load_dataset(dataset_url, split="train")
    validation_dataset = load_dataset(dataset_url, split="validation")

    # Combine into a DatasetDict
    dataset_dict = DatasetDict({"train": train_dataset, "test": validation_dataset})
    logging.info("Dataset loaded and combined into DatasetDict")

    # Tokenize the datasets with a progress bar
    def tokenize_function(examples):
        try:
            # Ensure the tokenizer has a pad token
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token

            # Adjust the sequence length and ensure proper truncation
            return tokenizer(
                examples["text"],
                truncation=True,
                padding="max_length",
                max_length=block_size,
                return_tensors="pt",  # Ensure the output is consistent in format
            )
        except Exception as e:
            logging.error(f"Error during tokenization: {e}")
            raise

    logging.info("Starting tokenization process")
    with tqdm(total=len(dataset_dict["train"])) as pbar:
        tokenized_datasets = dataset_dict.map(
            tokenize_function, batched=True, desc="Tokenizing"
        )
        pbar.update()

    logging.info("Tokenization completed")

    # Save tokenized datasets to disk with the dynamic dataset name
    save_path = (
        f"/home/ncacord/N.E.X.U.S.-Server/shared/data/tokenized_datasets/{dataset_name}"
    )
    tokenized_datasets.save_to_disk(save_path)
    logging.info(f"Tokenized dataset saved to {save_path}")

    print(f"Tokenized dataset saved to {save_path}")

except Exception as e:
    logging.error(f"An error occurred: {e}")
    print(f"An error occurred: {e}")
