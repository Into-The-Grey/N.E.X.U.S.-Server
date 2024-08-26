import torch
from torch.utils.data import Dataset, DataLoader
from transformers import AutoModelForCausalLM, AutoTokenizer, AdamW
from datasets import load_from_disk
import logging

# Setup logging
logging.basicConfig(
    filename="/home/ncacord/N.E.X.U.S.-Server/shared/logs/fine_tuning_debug.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Set the paths for the GPT-2 model and the tokenized dataset
model_path = "/home/ncacord/N.E.X.U.S.-Server/shared/models/gpt2"
dataset_path = "/home/ncacord/N.E.X.U.S.-Server/shared/data/tokenized_datasets/oasst1"

# Initialize the tokenizer and model
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(model_path)

# Enable CUDA if available
device = torch.device("cuda:0") if torch.cuda.is_available() else torch.device("cpu")  # Use the first GPU if CUDA is available, otherwise use CPU
if torch.cuda.is_available() and torch.cuda.device_count() > 1:
    model = torch.nn.DataParallel(model)  # Use DataParallel for multi-GPU
    device = torch.device("cuda:1")  # Use the second GPU if available

model.to(device)

# Load the tokenized dataset
try:
    dataset_dict = load_from_disk(dataset_path)
except Exception as e:
    logging.error(f"Failed to load dataset from disk. Error: {str(e)}")
    raise  # Re-raise the exception after logging

# Select the 'train' split
train_dataset = dataset_dict["train"]


# Define your custom dataset class
class CustomDataset(Dataset):
    def __init__(self, data):
        if not isinstance(data, list):
            raise TypeError("The 'data' parameter must be a list.")
        self.data = data

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        processed_item = {}
        if not isinstance(item, dict):
            raise TypeError("The 'item' parameter must be a dictionary.")
        for key, val in item.items():
            try:
                logging.debug(
                    f"Processing key: {key}, value type: {type(val)}, value: {val}"
                )
            except (TypeError, ValueError) as e:
                logging.error(
                    f"Failed to process key: {key} with value: {val}. Error: {e}"
                )
            if isinstance(val, (int, float, list)):  # Handle basic numeric types
                try:
                    processed_item[key] = torch.tensor(val, dtype=torch.float32)
                except Exception as e:
                    logging.error(
                        f"Failed to convert key: {key} with value: {val} to tensor. Error: {e}"
                    )
            elif isinstance(val, dict):  # Handle dictionaries by processing them
                flat_dict = {}
                for sub_key, sub_val in val.items():
                    if isinstance(sub_val, (int, float, list)):
                        try:
                            flat_dict[sub_key] = torch.tensor(sub_val)
                        except Exception as e:
                            logging.error(
                                f"Failed to convert nested key: {key}_{sub_key} with value: {sub_val} to tensor. Error: {e}"
                            )
                    elif isinstance(sub_val, str):
                        logging.debug(
                            f"Skipping nested key {key}_{sub_key} due to str type"
                        )
                    else:
                        logging.debug(
                            f"Skipping nested key {key}_{sub_key} due to incompatible type: {type(sub_val)}"
                        )
                processed_item[key] = flat_dict
            elif isinstance(val, str):
                logging.debug(f"Skipping key {key} due to str type")
            elif isinstance(val, torch.Tensor):
                processed_item[key] = val  # If it's already a tensor, use it directly
            else:
                logging.debug(
                    f"Skipping key {key} due to incompatible type: {type(val)}"
                )
                continue
        logging.debug(f"Processed item: {processed_item}")
        return processed_item


# Create an instance of your custom dataset using the 'train' split
custom_dataset = CustomDataset(train_dataset)

# Set the batch size
batch_size = 16  # Replace 16 with the desired batch size

# Create a data loader for batching and shuffling
data_loader = DataLoader(custom_dataset, batch_size=batch_size, shuffle=True)


# Define the training loop
def train():
    model.train()
    optimizer = AdamW(model.parameters(), lr=1e-5)
    num_epochs = 10  # Replace 10 with the desired number of epochs

    log_file = "/home/ncacord/N.E.X.U.S.-Server/shared/logs/training_loss.log"
    logging_handler = logging.FileHandler(log_file, mode="a")
    logging_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    if not any(isinstance(handler, logging.FileHandler) for handler in logging.getLogger().handlers):
        logging.getLogger().addHandler(logging_handler)
    
    for epoch in range(num_epochs):
        ...
        
        for batch_idx, batch in enumerate(data_loader):
            try:
                if "input_ids" not in batch:
                    logging.error("Key 'input_ids' not found in batch.")
                    continue
                if "labels" not in batch:
                    logging.error("Key 'labels' not found in batch.")
                    continue
        
                input_ids = batch["input_ids"].to(device)
                if "attention_mask" in batch:
                    attention_mask = batch["attention_mask"].to(device)
                else:
                    logging.error("Key 'attention_mask' not found in batch.")
                    continue
        
                labels = batch["labels"].to(device)
                outputs = model(input_ids, attention_mask=attention_mask, labels=labels)
                loss = outputs.loss
        
                # Remove the redundant check for "attention_mask"
                # if "attention_mask" not in batch:
                    logging.error("Key 'attention_mask' not found in batch.")
                    attention_mask = torch.ones_like(input_ids)  # Provide a default attention mask
                else:
                    attention_mask = batch["attention_mask"].to(device)
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                
                if not any(isinstance(handler, logging.FileHandler) for handler in logging.getLogger().handlers):
                    log_file = "/home/ncacord/N.E.X.U.S.-Server/shared/logs/training_loss.log"
                    logging_handler = logging.FileHandler(log_file, mode="a")
                    logging_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
                    logging.getLogger().addHandler(logging_handler)
        
                logging.info(f"Epoch {epoch+1}, Batch {batch_idx+1}, Loss: {loss.item()}")
            except Exception as e:
                logging.error(f"Error during training: {str(e)}")
                continue  # Continue to the next iteration of the training loop


# Run the training loop
try:
    train()
except Exception as e:
    logging.error(f"Error during training: {str(e)}")
    print(f"Error: {str(e)}")
