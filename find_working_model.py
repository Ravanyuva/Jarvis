import google.generativeai as genai
import os
import json

CANDIDATES = [
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-pro",
    "gemini-1.0-pro",
    "gemini-1.5-flash-latest",
    "gemini-1.5-pro-latest"
]

def find_model():
    try:
        if os.path.exists("jarvis_config.json"):
            with open("jarvis_config.json", "r") as f:
                config = json.load(f)
                api_key = config.get("GEMINI_API_KEY")
        
        if not api_key:
            print("No API key found.")
            return

        genai.configure(api_key=api_key)
        
        print("Testing models...")
        for model_name in CANDIDATES:
            print(f"Trying {model_name}...")
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content("Hello")
                print(f"SUCCESS: {model_name} works!")
                return
            except Exception as e:
                print(f"Failed {model_name}: {e}")
                
        # If all candidates fail, try listing again to see what IS there
        print("All candidates failed. Listing available raw models:")
        for m in genai.list_models():
            print(f" - {m.name}")

    except Exception as e:
        print(f"Global Error: {e}")

if __name__ == "__main__":
    find_model()
