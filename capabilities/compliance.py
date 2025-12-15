from .base import Capability

class ComplianceEngine(Capability):
    def name(self):
        return "Compliance Engine"

    def __init__(self, assistant):
        super().__init__(assistant)
        self.prohibited_actions = ["format_drive", "delete_system32", "crypto_mining"]

    def check_compliance(self, intent: dict) -> bool:
        # Check if action is prohibited
        action_type = intent.get("type", "")
        
        if action_type == "system_control":
            action = intent.get("action", "")
            if action in self.prohibited_actions:
                print(f"[COMPLIANCE] Blocked prohibited action: {action}")
                return False

        # Additional Geofencing or Policy checks could go here
        return True
