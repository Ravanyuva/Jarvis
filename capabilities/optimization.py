from .base import Capability
import time

class CostOptimizer(Capability):
    def name(self):
        return "Cost Optimizer"

    def __init__(self, assistant):
        super().__init__(assistant)
        self.token_usage = 0
        self.daily_limit = 100000 # Example token limit

    def track_usage(self, tokens: int):
        self.token_usage += tokens
        if self.token_usage > self.daily_limit:
            print("[COST] Warning: Daily token limit exceeded.")

    def optimize_prompt(self, text: str) -> str:
        """
        Simple heuristic: Truncate very long history or context if not critical.
        """
        if len(text) > 20000:
             print("[COST] Optimizing input length...")
             return text[:20000] + "... [TRUNCATED]"
        return text

    def on_input_received(self, text: str) -> str:
        return self.optimize_prompt(text)
