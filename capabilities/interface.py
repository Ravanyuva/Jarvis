from .base import Capability

class TransparencyEngine(Capability):
    def name(self):
        return "Transparency Engine"

    def __init__(self, assistant):
        super().__init__(assistant)
        self.transparency_level = 1 # 0: None, 1: Minimal, 2: Verbose

    def explain_decision(self, intent, confidence):
        if self.transparency_level > 0:
            return f"I decided to {intent['type']} because confidence is {confidence}."
        return ""
    
    # In a real UI, this would emit events to the frontend overlay
    def log_explanation(self, explanation):
        print(f"[EXPLAIN] {explanation}")
