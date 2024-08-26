import os
import torch
from torch.utils.data import DataLoader, Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments
from tqdm import tqdm
from datasets import load_from_disk
import torch.distributed as dist
import torch.multiprocessing as mp

# Load environment variables (if necessary)
from dotenv import load_dotenv

load_dotenv()

# Set the model and tokenizer
model_name = "gpt2"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

# Set the block size and batch size
block_size = 128
batch_size = 8

# Initialize multi-GPU training
if torch.cuda.device_count() > 1:
    model = torch.nn.DataParallel(model)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

# Load the tokenized dataset
dataset_name = "daily_dialog"
tokenized_dataset_path = (
    f"/home/ncacord/N.E.X.U.S.-Server/shared/data/tokenized_datasets/{dataset_name}"
)
tokenized_datasets = load_from_disk(tokenized_dataset_path)

# Split into train and validation datasets
tokenized_train = tokenized_datasets["train"]
tokenized_val = tokenized_datasets["validation"]


# Convert HuggingFace Dataset to PyTorch Dataset
class HuggingFaceDataset(Dataset):
    def __init__(self, hf_dataset):
        self.dataset = hf_dataset

    def __len__(self):
        return len(self.dataset)

    def __getitem__(self, idx):
        return {key: val[idx] for key, val in self.dataset.items()}


# Convert tokenized datasets to PyTorch Dataset
pytorch_train_dataset = HuggingFaceDataset(tokenized_train)
pytorch_val_dataset = HuggingFaceDataset(tokenized_val)

# Create DataLoaders for your PyTorch datasets with progress bars
train_dataloader = DataLoader(
    pytorch_train_dataset, shuffle=True, batch_size=batch_size
)
val_dataloader = DataLoader(pytorch_val_dataset, shuffle=False, batch_size=batch_size)

train_dataloader = tqdm(train_dataloader, desc="Training Progress")
val_dataloader = tqdm(val_dataloader, desc="Validation Progress")

# Training arguments
training_args = TrainingArguments(
    output_dir="/home/ncacord/N.E.X.U.S.-Server/shared/data/training_results",
    evaluation_strategy="steps",
    save_steps=10_000,
    save_total_limit=2,
    num_train_epochs=3,
    per_device_train_batch_size=batch_size,
    per_device_eval_batch_size=batch_size,
    warmup_steps=500,
    weight_decay=0.01,
    logging_dir="/home/ncacord/N.E.X.U.S.-Server/shared/logs",
    logging_steps=10,
    fp16=True,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=pytorch_train_dataset,
    eval_dataset=pytorch_val_dataset,
    tokenizer=tokenizer,
)

# Training loop with progress bars
print("Starting fine-tuning process...")
trainer.train()

# Save the model
save_model = input(
    "Would you like to save, this will overwrite the current model? (y/n): "
)
if save_model.lower() == "y":
    print("Saving model...")
    trainer.save_model(model_name)
    tokenizer.save_pretrained(model_name)
    print("Model saved.")
else:
    print("Exiting without saving.")
