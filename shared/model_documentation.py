import os
import torch
from transformers import AutoModel, AutoTokenizer
from pathlib import Path

# Define the models directory
models_dir = Path("/home/ncacord/N.E.X.U.S.-Server/shared/models")

# Define the output Markdown file
output_file = models_dir / "installed_models.md"

# Initialize Markdown content
md_content = "# Installed Models\n\n"

# Loop through all directories in the models directory
for model_name in os.listdir(models_dir):
    model_path = models_dir / model_name
    if model_path.is_dir():
        try:
            # Load model and tokenizer
            tokenizer = AutoTokenizer.from_pretrained(model_path)
            model = AutoModel.from_pretrained(model_path)

            # Get model size
            model_size = (
                sum(p.numel() for p in model.parameters()) * 4 / 1024**2
            )  # Size in MB
            model_size_str = f"{model_size:.2f} MB"

            # Add model details to markdown content
            md_content += f"## {model_name}\n"
            md_content += f"- **Model Path**: `{model_path}`\n"
            md_content += f"- **Size**: {model_size_str}\n"
            md_content += (
                f"- **Precision**: `Float32`\n"  # Assuming Float32 for simplicity
            )
            md_content += f"- **Tasks**: Masked Language Modeling (if applicable)\n\n"

        except Exception as e:
            md_content += f"## {model_name}\n"
            md_content += f"- **Model Path**: `{model_path}`\n"
            md_content += f"- **Error**: Could not load model. Error: {str(e)}\n\n"

# Save the Markdown content to a file
with open(output_file, "w") as f:
    f.write(md_content)

print(f"Model information written to {output_file}")
