from abc import ABC, abstractmethod

class Capability(ABC):
    """
    Abstract Base Class for all Jarvis Capabilities.
    """
    def __init__(self, assistant):
        self.assistant = assistant
        self.enabled = True

    @abstractmethod
    def name(self) -> str:
        """Return the unique name of this capability."""
        pass

    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False

    # Hooks - Override these in subclasses
    
    def on_start(self):
        """Called when Jarvis starts."""
        pass

    def on_input_received(self, text: str) -> str:
        """Called when raw user input is received. Return modified text or original."""
        return text

    def on_intent_parsed(self, intent: dict) -> dict:
        """Called after intent is parsed. Return modified intent or original."""
        return intent

    def check_compliance(self, intent: dict) -> bool:
        """
        Called before execution. Return True if safe/compliant, False to block.
        If blocked, the capability should log/notify why.
        """
        return True

    def on_action_execution(self, action_func, *args, **kwargs):
        """
        Called right before an action executes. 
        Can be used for auditing or sandboxing.
        """
        pass

    def on_output_generation(self, text: str) -> str:
        """Called before Jarvis speaks or prints. Return modified text."""
        return text

    def on_shutdown(self):
        """Called when Jarvis shuts down."""
        pass
