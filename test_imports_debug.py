try:
    import speech_recognition as sr
    print("sr imported")
except ImportError as e:
    print(f"sr failed: {e}")

try:
    import pyttsx3
    print("pyttsx3 imported")
except ImportError as e:
    print(f"pyttsx3 failed: {e}")

try:
    import keyboard
    print("keyboard imported")
except ImportError as e:
    print(f"keyboard failed: {e}")

try:
    import pyautogui
    print("pyautogui imported")
except ImportError as e:
    print(f"pyautogui failed: {e}")

try:
    import psutil
    print("psutil imported")
except ImportError as e:
    print(f"psutil failed: {e}")

try:
    import wikipedia
    print("wikipedia imported")
except ImportError as e:
    print(f"wikipedia failed: {e}")

try:
    from duckduckgo_search import DDGS
    print("DDGS imported")
except ImportError as e:
    print(f"DDGS failed: {e}")
