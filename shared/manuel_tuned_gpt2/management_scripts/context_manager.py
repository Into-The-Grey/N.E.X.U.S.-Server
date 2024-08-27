import csv
import os

# Paths for storing context data
context_file = "/home/ncacord/N.E.X.U.S.-Server/shared/manuel_tuned_gpt2/model_context_memory/context_data.csv"

class ContextManager:
    """Manages the session context for better prompt generation."""

    def __init__(self):
        self.context_memory = []
        self.load_context_memory()

    def load_context_memory(self):
        """Loads context memory from a file, if it exists."""
        if os.path.exists(context_file):
            with open(context_file, "r") as file:
                reader = csv.reader(file)
                self.context_memory = [row for row in reader]

    def save_context_memory(self):
        """Saves the current context memory to a file."""
        with open(context_file, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerows(self.context_memory)

    def add_to_context(self, prompt, response):
        """Adds a new interaction to the context memory."""
        self.context_memory.append([prompt, response])
        if len(self.context_memory) > 5:  # Limit context to last 5 interactions
            self.context_memory.pop(0)
        self.save_context_memory()

    def get_contextual_prompt(self, prompt):
        """Create a prompt that includes recent context."""
        context = " ".join([f"User: {p} Bot: {r}" for p, r in self.context_memory])
        return f"{context} User: {prompt}"


context_manager = ContextManager()
