import requests
import json

def check_ollama():
    try:
        # Check if running
        print("Checking Ollama availability...")
        resp = requests.get("http://localhost:11434/")
        if resp.status_code == 200:
            print("SUCCESS: Ollama is running.")
        else:
            print(f"WARN: Ollama responded with code {resp.status_code}")
            
        # List models
        print("Checking available models...")
        resp = requests.get("http://localhost:11434/api/tags")
        if resp.status_code == 200:
            models = resp.json().get("models", [])
            print(f"Found {len(models)} models:")
            for m in models:
                print(f" - {m.get('name')}")
        else:
            print("Could not list models.")
            
    except Exception as e:
        print(f"ERROR: Could not connect to Ollama: {e}")
        print("Make sure Ollama is installed and running (run 'ollama serve' in a terminal).")

if __name__ == "__main__":
    check_ollama()
