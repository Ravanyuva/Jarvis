from typing import List
import importlib
import os
import pkgutil

class CapabilityManager:
    def __init__(self, assistant):
        self.assistant = assistant
        self.capabilities = []

    def load_capabilities(self):
        """
        Dynamically loads all capability classes from the sibling modules.
        For now, we will explicitly import known ones to ensure order/stability.
        """
        # We will register them here as we build them.
        # from .privacy import PrivacyManager
        # self.register(PrivacyManager(self.assistant))
        pass

    def register(self, capability):
        self.capabilities.append(capability)
        print(f"[SYSTEM] Registered capability: {capability.name()}")
        capability.on_start()

    # --- Hook Orchestration ---

    def process_input(self, text: str) -> str:
        for cap in self.capabilities:
            if cap.enabled:
                text = cap.on_input_received(text)
        return text

    def process_intent(self, intent: dict) -> dict:
        for cap in self.capabilities:
            if cap.enabled:
                intent = cap.on_intent_parsed(intent)
        return intent

    def check_compliance(self, intent: dict) -> bool:
        for cap in self.capabilities:
            if cap.enabled:
                if not cap.check_compliance(intent):
                    print(f"[BLOCKED] Action blocked by {cap.name()}")
                    return False
        return True

    def process_output(self, text: str) -> str:
        for cap in self.capabilities:
            if cap.enabled:
                text = cap.on_output_generation(text)
        return text
    
    def shutdown(self):
        for cap in self.capabilities:
            cap.on_shutdown()
