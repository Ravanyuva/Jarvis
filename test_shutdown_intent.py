from jarvis_advanced import JarvisAssistant

print("Testing Shutdown Intent...")
jarvis = JarvisAssistant()

# Test cases
prompts = [
    "shutdown system",
    "turn off pc",
    "shutdown computer"
]

for p in prompts:
    intent = jarvis.parse_intent(p)
    print(f"Prompt: '{p}' -> Intent: {intent.get('type')} Action: {intent.get('action')}")

print("\n(Note: This only tests parsing. We won't execute handle_intent to avoid turning off your PC right now.)")
