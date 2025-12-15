import google.generativeai as genai
import os
import json

def list_models():
    try:
        if os.path.exists("jarvis_config.json"):
            with open("jarvis_config.json", "r") as f:
                config = json.load(f)
                api_key = config.get("GEMINI_API_KEY")
        
        if not api_key:
            print("No API key found in config.")
            return

        genai.configure(api_key=api_key)
        print("Listing available models:")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(m.name)
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_models()
