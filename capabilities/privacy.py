from .base import Capability
import re

class PrivacyManager(Capability):
    def name(self):
        return "Privacy Manager"

    def __init__(self, assistant):
        super().__init__(assistant)
        self.pii_patterns = [
            (r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]'),
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]'),
            (r'\b\d{3}-\d{3}-\d{4}\b', '[PHONE]'), # Dashed phone
            (r'\b\d{10}\b', '[PHONE]'), # Simple 10-digit phone
        ]
        self.anonymize_logs = True

    def on_input_received(self, text: str) -> str:
        # We might want to keep the raw input for processing but anonymize it for logs.
        # But if the user wants strict privacy, we scrub it immediately? 
        # For now, let's just scrub for logging purposes, but return original for processing.
        # Actually, let's assume 'text' here is passed down the pipeline.
        # If we scrub here, the AI won't see the email to send a message to.
        # So we should only scrub for *logs* or *external* storage.
        # The 'on_input_received' hook in our manager changes the input *flowing into the system*.
        # So we probably shouldn't scrub here unless we want to block PII from reaching the LLM (for local-only privacy).
        return text

    def anonymize(self, text: str) -> str:
        if not self.anonymize_logs:
            return text
        for pattern, replacement in self.pii_patterns:
            text = re.sub(pattern, replacement, text)
        return text

    # We will need a specific hook for logging if we want to enforce it there.
    # For now, let's assume this class is accessible by the logger.
