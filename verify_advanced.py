from database import db
from jarvis_advanced import JarvisAssistant
import time

def verify_all():
    print("--- 1. DATABASE TEST (SQLite) ---")
    if db.set_preference("test_key", "test_value"):
        val = db.get_preference("test_key")
        if val == "test_value":
            print("[SUCCESS] SQLite Preference Set/Get working.")
        else:
            print(f"[FAIL] Retrieved value mismatch: {val}")
    else:
        print("[FAIL] Failed to set preference.")
        
    print("\n--- 2. JARVIS INIT ---")
    try:
        assistant = JarvisAssistant()
        print("[SUCCESS] Jarvis Initialized.")
        
        # Check Vision Init
        if assistant.vision:
             print("[SUCCESS] Vision System Initialized.")
        else:
             print("[FAIL] Vision System is None.")
             
        # Mock Intent Check
        print("\n--- 3. MEMORY INTENT CHECK ---")
        mock_intent = {"type": "memory_set", "key": "user_name", "value": "Tony Stark"}
        assistant.handle_intent(mock_intent)
        
        stored_name = db.get_preference("user_name")
        if stored_name == "Tony Stark":
             print("[SUCCESS] Memory Intent logic working.")
        else:
             print(f"[FAIL] Memory Intent failed. Stored: {stored_name}")

    except Exception as e:
        print(f"[CRITICAL FAIL] Logic crash: {e}")

if __name__ == "__main__":
    verify_all()
