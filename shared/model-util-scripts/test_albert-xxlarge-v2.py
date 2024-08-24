import torch
from transformers import AutoModelForMaskedLM, AutoTokenizer
import time
import subprocess


def check_vram_usage():
    try:
        output = subprocess.check_output(
            "nvidia-smi --query-gpu=memory.used --format=csv,nounits,noheader",
            shell=True,
        )
        vram_usage = int(output.decode("utf-8").split("\n")[0].strip())
        return vram_usage
    except Exception as e:
        print(f"An error occurred while checking VRAM usage: {str(e)}")
        return None


def load_test(model, tokenizer, load_level):
    masked_sentence = "The capital of France is [MASK]."
    input_ids = tokenizer.encode(masked_sentence, return_tensors="pt").repeat(
        load_level, 1
    )

    # Move input_ids to the same device as the model
    device = next(model.parameters()).device
    input_ids = input_ids.to(device)

    print(f"Starting low load test with load level: {load_level}")
    start_vram = check_vram_usage()
    _ = model(input_ids)
    end_vram = check_vram_usage()
    if start_vram is not None and end_vram is not None:
        print(f"Low load test VRAM usage: {end_vram - start_vram} MiB")
    else:
        print("Failed to measure VRAM usage.")


def main():
    model_path = "/home/ncacord/N.E.X.U.S.-Server/shared/models/albert-xxlarge-v2"
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForMaskedLM.from_pretrained(model_path).to("cuda:1")

    # Warm-up (low load)
    load_test(model, tokenizer, load_level=1)

    # Medium load test
    time.sleep(2)  # Give the GPU some time to cool down
    load_test(model, tokenizer, load_level=8)


if __name__ == "__main__":
    main()
