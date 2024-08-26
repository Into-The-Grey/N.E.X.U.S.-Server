import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
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


def load_test(model, tokenizer, load_level, num_generations=5):
    input_text = "Once upon a time in a land far, far away"
    input_ids = tokenizer.encode(input_text, return_tensors="pt").repeat(load_level, 1)

    # Move input_ids to the same device as the model
    device = next(model.parameters()).device
    input_ids = input_ids.to(device)

    print(f"Starting load test with load level: {load_level}")
    start_vram = check_vram_usage()

    generated_texts = []
    for _ in range(num_generations):
        outputs = model.generate(input_ids, max_length=100)
        generated_texts.append(tokenizer.decode(outputs[0], skip_special_tokens=True))

    end_vram = check_vram_usage()

    if start_vram is not None and end_vram is not None:
        print(f"Load test VRAM usage: {end_vram - start_vram} MiB")
    else:
        print("Failed to measure VRAM usage.")

    # Display a sample of the generated text to verify the model is working
    print("\nSample of generated text:")
    for i, text in enumerate(generated_texts, 1):
        print(f"Sample {i}: {text[:200]}...")


def main():
    model_path = "/home/ncacord/N.E.X.U.S.-Server/shared/models/gpt2"
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(model_path).to("cuda:1")

    # Warm-up (low load)
    load_test(model, tokenizer, load_level=1)

    # Medium load test
    time.sleep(2)  # Give the GPU some time to cool down
    load_test(model, tokenizer, load_level=8, num_generations=3)


if __name__ == "__main__":
    main()
