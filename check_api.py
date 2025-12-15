import google.generativeai as genai
import os
import json

def check_gemini():
    try:
        # Load config to get key
        if os.path.exists("jarvis_config.json"):
            with open("jarvis_config.json", "r") as f:
                config = json.load(f)
                api_key = config.get("GEMINI_API_KEY")
        else:
            print("Config missing.")
            return

        if not api_key or api_key == "PASTE_YOUR_API_KEY_HERE":
            print("API Key not configured.")
            return

        print(f"Testing Key: {api_key[:5]}...")
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content("Say 'OK'")
        print(f"Success. Response: {response.text}")

    except Exception as e:
        print(f"API Error: {e}")

if __name__ == "__main__":
    check_gemini()
