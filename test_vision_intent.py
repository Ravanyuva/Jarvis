from jarvis_advanced import JarvisAssistant

print("Testing Vision Intents...")
try:
    jarvis = JarvisAssistant()
    
    prompts = [
        "activate vision",
        "enable virtual keyboard",
        "start mouse control",
        "gesture control",
        "jarvis enable vision"
    ]
    
    for p in prompts:
        print(f"\nPrompt: '{p}'")
        intent = jarvis.parse_intent(p)
        print(f" -> Type: {intent.get('type')}")
        print(f" -> Action: {intent.get('action')}")
        print(f" -> Mode: {intent.get('mode')}")
        
except Exception as e:
    print(f"Error: {e}")
