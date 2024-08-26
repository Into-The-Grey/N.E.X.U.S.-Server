import os
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import AutoModelForCausalLM, AutoTokenizer, AdamW
from datasets import load_from_disk

# Set the paths for the GPT-2 model and the tokenized dataset
model_path = "/home/ncacord/N.E.X.U.S.-Server/shared/models/gpt2"
dataset_path = "/home/ncacord/N.E.X.U.S.-Server/shared/data/tokenized_datasets/oasst1"

# Set the path for the log directory and file
log_file = "/home/ncacord/N.E.X.U.S.-Server/shared/logs/fine_tuning.log"

# Initialize the tokenizer and model
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(model_path)

# Enable CUDA if available
device = torch.device(torch.cuda.is_available() and "cuda" or "cpu")
model.to(device)

# Load the tokenized dataset
dataset = load_from_disk(dataset_path)


# Define your custom dataset class
class CustomDataset(Dataset):
    def __init__(self, data):
        self.data = data

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        return {
            "input_ids": torch.tensor(item["input_ids"], dtype=torch.long),
            "attention_mask": torch.tensor(item["attention_mask"]),
            "labels": torch.tensor(item["labels"]),
        }


# Create an instance of your custom dataset
custom_dataset = CustomDataset(dataset)

# Create a data loader for batching and shuffling
data_loader = DataLoader(custom_dataset, batch_size=16, shuffle=True)


# Define the training loop
def train():
    # Set the model to training mode
    model.train()

    # Define the optimizer
    learning_rate = 1e-5  # Set the desired learning rate here
    optimizer = AdamW(model.parameters(), lr=learning_rate)

    # Define the number of epochs
    num_epochs = 10  # Replace 10 with the desired number of epochs
    
    # Define the gradient accumulation steps
    gradient_accumulation_steps = 1  # Replace 1 with the desired number of gradient accumulation steps
    
    # Start the training loop
    for epoch in range(num_epochs):
        accumulated_loss = 0
        for batch_idx, batch in enumerate(data_loader):
            # Move the batch to the device
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)
    
            # Forward pass
            outputs = model(
                input_ids=input_ids, attention_mask=attention_mask, labels=labels
            )
    
            # Compute the loss
            loss = outputs.loss
    
            # Accumulate the loss
            accumulated_loss += loss
    
            if (batch_idx + 1) % gradient_accumulation_steps == 0:
                # Backward pass and optimization
                optimizer.zero_grad()
                accumulated_loss.backward()
                optimizer.step()
    
                # Log the loss
                with open(log_file, "a") as f:
                    f.write(f"Epoch {epoch+1}, Batch {batch_idx+1}, Loss: {accumulated_loss.item()}\n")
    
            # Close the log file
            f.close()
    
            # Reset the accumulated loss
            accumulated_loss = 0
    
        # Check if there are remaining accumulated gradients
        if accumulated_loss != 0:
            # Backward pass and optimization
            optimizer.zero_grad()
            accumulated_loss.backward()
            optimizer.step()
    
            # Log the loss
            with open(log_file, "a") as f:
                f.write(f"Epoch {epoch+1}, Batch {batch_idx+1}, Loss: {accumulated_loss.item()}\n")


# Run the training loop
try:
    train()
except Exception as e:
    # Handle any exceptions and log the error
    with open(log_file, "a") as f:
        f.write(f"Error: {str(e)}\n")
    # Print the error message to the console
    print(f"Error: {str(e)}")
