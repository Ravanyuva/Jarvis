import google.generativeai as genai
import os
import json

def find_model():
    try:
        if os.path.exists("jarvis_config.json"):
            with open("jarvis_config.json", "r") as f:
                config = json.load(f)
                api_key = config.get("GEMINI_API_KEY")
        
        if not api_key:
            with open("working_model_info.txt", "w", encoding="utf-8") as f:
                f.write("No API key found.")
            return

        genai.configure(api_key=api_key)
        
        output = []
        output.append("Listing available models:")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                output.append(f" - {m.name}")
        
        with open("working_model_info.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(output))

    except Exception as e:
        with open("working_model_info.txt", "w", encoding="utf-8") as f:
            f.write(f"Global Error: {e}")

if __name__ == "__main__":
    find_model()
