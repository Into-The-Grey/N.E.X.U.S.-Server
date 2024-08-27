import random

def strict_format(response, variations):
    chosen_variation = random.choice(variations)
    return f"({chosen_variation} {response})"
