from .base import Capability
import time
import json
import os

class ActionProvenance(Capability):
    def name(self):
        return "Action Provenance"

    def __init__(self, assistant):
        super().__init__(assistant)
        self.log_file = "provenance_log.jsonl"

    def log_action(self, intent, outcome="pending"):
        entry = {
            "timestamp": time.time(),
            "intent": intent,
            "outcome": outcome,
            "user": "primary_user" # Multi-user support later
        }
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            print(f"[PROVENANCE] Log failed: {e}")

    def on_intent_parsed(self, intent: dict) -> dict:
        # Log the intent as soon as it's understood
        self.log_action(intent, "parsed")
        return intent
