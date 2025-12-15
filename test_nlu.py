import jarvis_advanced
import json
import time

def test_parsing():
    print("Initializing Jarvis...")
    # Mock config loading to ensure we have a provider
    # Assuming config.json exists and has valid keys, or defaults will work.
    # We might need to ensure API key is present for Gemini or Ollama is running.
    
    app = jarvis_advanced.JarvisAssistant()
    
    test_cases = [
        {"input": "open youtube", "expected_type": "open_something", "expected_target": "youtube"}, # Regex
        {"input": "open youtube please", "expected_type": "open_something", "expected_target": "youtube"}, # Politeness Stripping
        {"input": "can you play some music", "expected_type": "play_music", "expected_target": None}, # AI
        {"input": "shutdown the system please", "expected_type": "system_control", "expected_action": "shutdown"}, # AI
        {"input": "what is the time", "expected_type": "get_time", "expected_target": None}, # Regex or AI
        
        # New Regression Tests
        {"input": "open virtual keyboard", "expected_type": "vision_control", "expected_target": None}, # Should be vision, NOT open_something
        {"input": "virtual keyboard", "expected_type": "vision_control", "expected_target": None}, 
        {"input": "shutdown", "expected_type": "system_control", "expected_action": "shutdown"},
        {"input": "play ishq song from youtube", "expected_type": "play_music", "expected_target": "ishq song"}, # Stripped "from youtube"
    ]
    
    with open("summary.txt", "w") as f:
        f.write("--- Test Summary ---\n")
        print("\n--- Starting Tests ---\n")
        for case in test_cases:
            text = case["input"]
            print(f"Testing: '{text}'")
            intent = app.parse_intent(text)
            
            result_line = f"Input: '{text}' -> Intent: {intent['type']}"
            passed = True
            
            if intent["type"] != case["expected_type"]:
                passed = False
                result_line += f" [FAIL: Expected {case['expected_type']}]"
            
            if "expected_target" in case and case["expected_target"]:
                 tgt = intent.get("target") or intent.get("song") or intent.get("action")
                 if not tgt or case["expected_target"] not in tgt:
                     passed = False
                     result_line += f" [FAIL: Target '{tgt}' != '{case['expected_target']}']"
            
            if passed:
                result_line += " [PASS]"
            
            print(result_line)
            f.write(result_line + "\n")

if __name__ == "__main__":
    test_parsing()
