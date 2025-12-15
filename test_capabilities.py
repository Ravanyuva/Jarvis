import unittest
from jarvis_advanced import JarvisAssistant
from capabilities.manager import CapabilityManager

class TestCapabilities(unittest.TestCase):
    def setUp(self):
        # Initialize Jarvis (might need mocking for heavy stuff like chrome)
        # We will assume config is present or defaults work.
        self.jarvis = JarvisAssistant()
        # Disable vision to speed up
        self.jarvis.vision = None 

    def test_privacy(self):
        # Direct test of privacy manager
        # Find the capability
        priv_man = next(c for c in self.jarvis.capabilities.capabilities if c.name() == "Privacy Manager")
        
        # Test basic flow (currently it just passes through on input, but let's test anonymize logic directly)
        # Test basic flow
        text = "My ID is 123-45-6789"
        # We didn't expose anonymize in the manager input hook, but the method exists on the class
        anonymized = priv_man.anonymize("My ID is 123-45-6789")
        self.assertIn("[SSN]", anonymized)
        # Let's test the regex carefully. 123-456-7890 matches standard phone? 
        # The privacy.py had: (r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]') 
        # and (r'\b\d{10}\b', '[PHONE]')
        
        # Test SSN
        self.assertEqual(priv_man.anonymize("ID: 123-45-6789"), "ID: [SSN]")
        
        # Test Phone (10 digit)
        self.assertEqual(priv_man.anonymize("Call 9999999999"), "Call [PHONE]")

    def test_compliance(self):
        # Test blocking
        intent = {"type": "system_control", "action": "format_drive"}
        allowed = self.jarvis.capabilities.check_compliance(intent)
        self.assertFalse(allowed)

        intent_ok = {"type": "system_control", "action": "restart"}
        allowed_ok = self.jarvis.capabilities.check_compliance(intent_ok)
        self.assertTrue(allowed_ok)

    def test_provenance(self):
        # Check if log is created
        import os
        if os.path.exists("provenance_log.jsonl"):
            os.remove("provenance_log.jsonl")
            
        intent = {"type": "greeting"}
        # This hook runs manually in our current setup or via process_intent if we wired it
        prov = next(c for c in self.jarvis.capabilities.capabilities if c.name() == "Action Provenance")
        prov.on_intent_parsed(intent)
        
        self.assertTrue(os.path.exists("provenance_log.jsonl"))

if __name__ == '__main__':
    unittest.main()
