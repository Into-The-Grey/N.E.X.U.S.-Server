class ContextManager:
    """Manages the session context for better prompt generation."""

    def __init__(self):
        self.context_memory = []

    def add_to_context(self, prompt, response):
        """Add a new interaction to the context memory."""
        self.context_memory.append((prompt, response))
        if len(self.context_memory) > 5:  # Limit context to last 5 interactions
            self.context_memory.pop(0)

    def get_contextual_prompt(self, prompt):
        """Create a prompt that includes recent context."""
        context = " ".join([f"User: {p} Bot: {r}" for p, r in self.context_memory])
        return f"{context} User: {prompt}"


context_manager = ContextManager()
