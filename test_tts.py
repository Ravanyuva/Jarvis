import pyttsx3
try:
    engine = pyttsx3.init()
    print("Engine initialized.")
    engine.say("Testing audio output.")
    engine.runAndWait()
    print("Speak command finished.")
except Exception as e:
    print(f"Error: {e}")
