try:
    import speech_recognition as sr
    print("SpeechRecognition imported")
    import pyttsx3
    print("pyttsx3 imported")
    import keyboard
    print("keyboard imported")
    import pyautogui
    print("pyautogui imported")
    import pyaudio
    print("pyaudio imported")
    print("ALL OK")
except Exception as e:
    print(f"IMPORT ERROR: {e}")
