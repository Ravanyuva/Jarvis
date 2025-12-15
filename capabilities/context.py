from .base import Capability

class ContextAwareness(Capability):
    def name(self):
        return "Context Awareness"

    def __init__(self, assistant):
        super().__init__(assistant)
        self.current_user = "primary_user"
        self.environment_mode = "unknown" # e.g., quiet, busy

    def set_environment_context(self, noise_level):
        if noise_level > 80:
            self.environment_mode = "noisy"
        else:
            self.environment_mode = "quiet"

class AccessibilityManager(Capability):
    def name(self):
        return "Accessibility Manager"

    def __init__(self, assistant):
        super().__init__(assistant)
        self.voice_only = False
        self.speech_rate = 150

    def toggle_voice_only(self):
        self.voice_only = not self.voice_only
        print(f"[ACCESSIBILITY] Voice only mode: {self.voice_only}")

    def on_output_generation(self, text: str) -> str:
        # Could adjust speech style here if needed
        return text
