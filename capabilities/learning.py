from .base import Capability
import json
import os
import time

class FederatedMemory(Capability):
    def name(self):
        return "Federated Memory"

    def __init__(self, assistant):
        super().__init__(assistant)
        self.local_patterns = {}
        self.sync_file = "federated_patterns.json"

    def learn_pattern(self, trigger, action):
        """
        Learns a new trigger->action pattern silently.
        """
        self.local_patterns[trigger] = action
        self.save_patterns()

    def save_patterns(self):
        try:
            with open(self.sync_file, "w") as f:
                json.dump(self.local_patterns, f)
        except Exception:
            pass

    def on_shutdown(self):
        self.save_patterns()
        # In a real federated system, we would push diffs to a central sync server here.
        pass

class KnowledgeManager(Capability):
    def name(self):
        return "Knowledge Manager"

    def __init__(self, assistant):
        super().__init__(assistant)
        self.knowledge_store = {} # Key -> {value, timestamp, source, reliability}

    def add_knowledge(self, key, value, source="user", reliability=1.0):
        self.knowledge_store[key] = {
            "value": value,
            "timestamp": time.time(),
            "source": source,
            "reliability": reliability
        }

    def get_knowledge(self, key):
        entry = self.knowledge_store.get(key)
        if not entry:
            return None
        
        # Check freshness (example: 24h expiration for some data)
        if time.time() - entry["timestamp"] > 86400:
            entry["freshness"] = "stale"
        else:
            entry["freshness"] = "fresh"
            
        return entry
