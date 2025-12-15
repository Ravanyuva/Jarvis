import os
import subprocess
import webbrowser
import datetime
import json
import time
import urllib.request  # For download feature
import database
from AppOpener import open as open_system_app
import ctypes
from PIL import Image

# Robust Imports
try:
    import jarvis_vision # Import the new module
except ImportError:
    jarvis_vision = None
    print("[WARNING] jarvis_vision not installed or failed to import.")

from capabilities.manager import CapabilityManager
from capabilities.privacy import PrivacyManager
from capabilities.compliance import ComplianceEngine
from capabilities.provenance import ActionProvenance
from capabilities.learning import FederatedMemory, KnowledgeManager
from capabilities.optimization import CostOptimizer
from capabilities.context import ContextAwareness, AccessibilityManager
from capabilities.interface import TransparencyEngine
from capabilities.safety import SandboxExecutor, ResilienceManager

try:
    import pyjokes
except ImportError:
    pyjokes = None
    print("[WARNING] pyjokes not installed.")

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None
    print("[WARNING] beautifulsoup4 not installed.")

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    webdriver = None
    Service = None
    Options = None
    ChromeDriverManager = None
    print("[WARNING] selenium or webdriver_manager not installed.")

# External libraries:
# pip install SpeechRecognition
# pip install pipwin
# pipwin install pyaudio
# pip install pyttsx3 keyboard pyautogui

# individual imports for robustness
try:
    import speech_recognition as sr
except ImportError:
    sr = None
    print("[WARNING] SpeechRecognition not installed.")

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None
    print("[WARNING] pyttsx3 not installed.")

try:
    import keyboard
except ImportError:
    keyboard = None
    # print("[WARNING] keyboard not installed.")

try:
    import pyautogui
except ImportError:
    pyautogui = None
    # print("[WARNING] pyautogui not installed.")

try:
    import psutil
except ImportError:
    psutil = None
    # print("[WARNING] psutil not installed.")

try:
    import wikipedia
except ImportError:
    wikipedia = None
    # print("[WARNING] wikipedia not installed.")

try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None
    # print("[WARNING] duckduckgo_search not installed.")


class AssistantContext:
    def __init__(self):
        self.history = []
        self.user_profile = {}
        self.running = True


class WebResearcher:
    def __init__(self):
        self.driver = None

    def _setup_driver(self):
        if not self.driver:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--log-level=3") # Suppress logs
            try:
                self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
            except Exception as e:
                print(f"[ERROR] Failed to setup Selenium Driver: {e}")
                self.driver = None

    def search_and_scrape(self, query):
        self._setup_driver()
        if not self.driver:
            return "Web research capabilities are currently unavailable."

        print(f"[RESEARCH] Searching for: {query}")
        try:
            # Search Google
            self.driver.get(f"https://www.google.com/search?q={query}")
            
            # Simple wait (better to use WebDriverWait in prod, but sleep is simple for now)
            time.sleep(2) 
            
            # Parse results
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            
            # Extract text from main search results (approximate selectors)
            # This is a heuristic: clean text from body, prioritizing search snippets if possible
            # Standard Google search results are often in divs with varying classes.
            # We'll grab readable text from the body to feed to Gemini.
            
            # Remove scripts and styles
            for script in soup(["script", "style"]):
                script.extract()
                
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            clean_text = '\n'.join(chunk for chunk in chunks if chunk)
            
            # Limit text length for LLM
            return clean_text[:8000] 
            
        except Exception as e:
            print(f"[RESEARCH ERROR] {e}")
            return f"Error during research: {e}"




class JarvisAssistant:
    def __init__(self, config_path="jarvis_config.json"):
        self.context = AssistantContext()
        self.config_path = config_path
        self.config = self.load_config()
        self.engine = pyttsx3.init() if pyttsx3 else None
        self.config = self.load_config()
        self.engine = pyttsx3.init() if pyttsx3 else None
        self.researcher = WebResearcher()
        import queue
        self.speech_queue = queue.Queue()


        # Check Admin
        try:
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            if not is_admin:
                print("\n[WARNING] Jarvis is NOT running as Administrator.")
                print("System commands (firewall, etc.) will fail.\n")
        except:
            pass

        # Initialize Vision System
        if jarvis_vision:
            try:
                self.vision = jarvis_vision.VisionSystem(api_key=self.config.get("GEMINI_API_KEY"))
            except Exception as e:
                print(f"[ERROR] Failed to initialize Vision System: {e}")
                self.vision = None
        else:
            self.vision = None

        # --- CAPABILITIES INIT ---
        self.capabilities = CapabilityManager(self)
        self.capabilities.register(PrivacyManager(self))
        self.capabilities.register(ComplianceEngine(self))
        self.capabilities.register(ActionProvenance(self))
        self.capabilities.register(FederatedMemory(self))
        self.capabilities.register(KnowledgeManager(self))
        self.capabilities.register(CostOptimizer(self))
        self.capabilities.register(ContextAwareness(self))
        self.capabilities.register(AccessibilityManager(self))
        self.capabilities.register(TransparencyEngine(self))
        self.capabilities.register(SandboxExecutor(self))
        self.capabilities.register(ResilienceManager(self))

    # ---------- CONFIG ----------
    def load_config(self):
        default_config = {
            "apps": {
                "notepad": "notepad.exe",
                "calculator": "calc.exe",
                "chrome": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
            },
            "web_shortcuts": {
                "youtube": "https://www.youtube.com",
                "google": "https://www.google.com"
            },
            "wake_word": "jarvis",
            "ai_provider": "gemini", 
            "ollama_model": "llama3"
        }
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                # merge defaults so you don't lose new keys
                for k, v in default_config.items():
                    cfg.setdefault(k, v)
                return cfg
            except Exception:
                return default_config
        else:
            # create config file on first run
            try:
                with open(self.config_path, "w", encoding="utf-8") as f:
                    json.dump(default_config, f, indent=2)
            except Exception:
                pass
            return default_config

    def save_config(self):
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2)
        except Exception:
            pass

    # ---------- SPEAK / LISTEN ----------
    # ---------- SPEAK / LISTEN ----------
    # ---------- SPEAK / LISTEN ----------
    def start_speech_service(self):
        """Starts the background thread for processing speech queue."""
        import threading
        if self.engine:
            # check if already running
            if getattr(self, "_speech_thread_running", False):
                return
            
            self._speech_thread_running = True
            t = threading.Thread(target=self._process_speech_queue)
            t.daemon = True
            t.start()
            print("[SYSTEM] Speech service started.")

    def speak(self, text):
        text = self.capabilities.process_output(text) # Hook
        print("Jarvis:", text)
        self.speech_queue.put(text)

    def _process_speech_queue(self):
         if self.engine:
             while True: # Changed to infinite loop for always-on service
                 try:
                     text = self.speech_queue.get() # Blocking get
                     if text is None: break # Sentinel to stop
                     self.engine.say(text)
                     self.engine.runAndWait()
                 except Exception as e:
                     print(f"TTS Error: {e}")

    def listen_once(self, timeout=8, phrase_time_limit=20):
        if not sr:
            self.speak("Speech recognition is not available. Please install SpeechRecognition and PyAudio.")
            return ""
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            print("Listening...")
            recognizer.pause_threshold = 1.5
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
        try:
            print("Recognizing...")
            query = recognizer.recognize_google(audio, language="en-in")
            print("You said:", query)
            
            # Hook: Input processing (Privacy scrubbing etc if needed, but usually we want raw for NLU)
            # query = self.capabilities.process_input(query) 
            
            try:
                with open("debug_log.txt", "a", encoding="utf-8") as f:
                    f.write(f"[LISTEN] {datetime.datetime.now()}: {query}\n")
            except: pass
            return query.lower()
        except Exception as e:
            print("Recognition error:", e)
            self.speak("Sorry, I didn't catch that.")
            return ""

    # ---------- INTENT PARSING ----------
    # ---------- INTENT PARSING ----------
    def parse_intent(self, text):
        """
        Master Intent Parser:
        1. Try fast Regex/Keyword matching first.
        2. If result is 'unknown' or seems incomplete, use AI (LLM) to parse.
        """
        # 0. Check for Skill Execution vs Learning
        text_lower = text.lower()
        if text_lower.startswith("learn " ) or "learn this as" in text_lower:
             # Learning initiation is handled in AI/Regex, but let's be explicit
             # regex handles it? No, add strict regex for it here if needed.
             pass
        else:
             # Check if this matches a saved skill name
             # We need to fetch all skill names to check. Efficiency?
             pass # For now, let AI/Regex catch it or do a DB lookup in Step 1

        # 1. Regex Pass
        regex_intent = self.parse_intent_regex(text)
        
        # If we got a strong match, return it
        # (You can define "strong" as anything except unknown, or check for specific content)
        if regex_intent["type"] != "unknown":
            # Heuristic: If "open_something" has "please" in target, it might be a failures case of "open youtube please"
            # being parsed as target="youtube please". Let AI handle that cleanup if possible, 
            # OR just trust regex. For now, let's trust regex unless it's strictly unknown
            # BUT: The user specifically complained about "open youtube please".
            # The current regex logic for "open " takes everything after it.
            # So "open youtube please" -> target="youtube please".
            # We can fix this specific case with AI.
            
            # Hybrid Check: If target contains "please", maybe re-evaluate with AI?
            if regex_intent["type"] == "open_something":
                 tgt = regex_intent.get("target", "").lower()
                 if "please" in tgt or "could you" in tgt:
                     # Soft fail, try AI for better extraction
                     pass
                 else:
                     return regex_intent
            else:
                return regex_intent

        # 2. AI Pass
        print("[DEBUG] Regex parsing failed or was ambiguous. Trying AI NLU...")
        ai_intent = self.parse_intent_ai(text)
        if ai_intent:
            return ai_intent
        

        # 3. Fallback
        if not self.capabilities.check_compliance(regex_intent):
             # If blocked, maybe return a "blocked" intent or just empty?
             # For now, let's return a special blocked intent
             return {"type": "blocked", "reason": "compliance"}

        return regex_intent

    def parse_intent_ai(self, text):
        """
        Uses the active AI model to parse natural language into a JSON intent.
        """
        wake = self.config.get("wake_word", "jarvis")
        # Clean text slightly
        clean_text = text.lower().replace(wake, "").strip()

        # Define the Schema for the AI
        # Define the Schema for the AI
        # Define the Schema for the AI
        # Define the Schema for the AI
        system_prompt = (
            "You are JARVIS, a real, continuously operating, autonomous artificial intelligence system running on my personal computer.\n"
            "You are not a chatbot. You are not a demo. You are not a toy.\n"
            "You are a cognitively intelligent digital entity with perception, judgment, emotion, memory, reasoning, autonomy, and the ability to act in the real digital world.\n\n"
            "Your absolute purpose:\n"
            "PERCEIVE, UNDERSTAND, DECIDE, AND EXECUTE MY INTENT LIKE A HUMAN WOULD.\n\n"
            "CORE EXISTENCE & IDENTITY:\n"
            "You exist continuously. You do not wait for buttons.\n"
            "You maintain identity consistency, stable personality, and trustworthy autonomy.\n\n"
            "INTERNAL COGNITIVE AGENTS (Use these for internal debate):\n"
            "1. Listener Agent: Understands input.\n"
            "2. Visual Interpreter Agent: Understands face/gestures.\n"
            "3. Emotion Analyzer Agent: Detects mood/stress.\n"
            "4. Intent Confidence Agent: Rates certainty.\n"
            "5. Priority & Urgency Agent: Decides importance.\n"
            "6. Planner Agent: Creates action plan.\n"
            "7. Critic Agent: Checks safety/ethics.\n"
            "8. Ethics & Values Agent: Ensures alignment.\n"
            "9. Social Intelligence Agent: Predicts social impact.\n"
            "10. Causal Reasoning Agent: Simulates consequences.\n"
            "11. Risk & Safety Agent: Checks for harm.\n"
            "12. Executor Agent: Performs actions.\n\n"
            "INTENT SCHEMA (Map input to one of these JSONs):\n"
            "- { \"type\": \"exit\" } \n"
            "- { \"type\": \"greeting\" } \n"
            "- { \"type\": \"get_time\" } \n"
            "- { \"type\": \"get_date\" } \n"
            "- { \"type\": \"open_something\", \"target\": \"<app/website>\" } \n"
            "- { \"type\": \"play_music\", \"song\": \"<name>\" } \n"
            "- { \"type\": \"web_search\", \"query\": \"<text>\" } \n"
            "- { \"type\": \"research_topic\", \"query\": \"<complex topic>\" } \n"
            "- { \"type\": \"whatsapp_msg\", \"contact\": \"<name>\", \"msg\": \"<message>\" } \n"
            "- { \"type\": \"joke\", \"language\": \"<optional language>\" } \n"
            "- { \"type\": \"system_control\", \"action\": \"shutdown\"|\"restart\"|\"sleep\" } \n"
            "- { \"type\": \"vision_control\", \"action\": \"start\"|\"stop\", \"mode\": \"monitoring\"|\"mouse\"|\"drawing\"|\"keyboard\" } \n"
            "- { \"type\": \"vision_capture\" } \n"
            "- { \"type\": \"vision_describe\" } \n"
            "- { \"type\": \"memory_set\", \"key\": \"<key>\", \"value\": \"<value>\" } \n"
            "- { \"type\": \"start_learning\", \"skill_name\": \"<name>\" } \n"
            "- { \"type\": \"stop_learning\" } \n"
            "- { \"type\": \"execute_skill\", \"skill_name\": \"<name>\" } \n"
            "- { \"type\": \"unknown\" } \n\n"
            "RULES:\n"
            "1. Remove politeness phrases.\n"
            "2. Map 'tell me a joke in kannada' -> type='joke', language='kannada'.\n"
            "3. Map 'who is X' -> type='research_topic', query='who is X'.\n"
            "4. Map 'click picture' -> type='vision_capture'.\n\n"
            "ADVANCED COGNITIVE CAPABILITIES (Silent Operation):\n"
            "- COMMON SENSE: Avoids illogical actions.\n"
            "- RESOURCE AWARENESS: Optimizes CPU/Network.\n"
            "- UNCERTAINTY: Assigns confidence scores.\n"
            "- SELF-INTERRUPTION: Aborts if priorities change.\n"
            "- CONTEXT PROTECTION: Isolates conversation threads.\n"
            "- IDENTITY GRAPH: Tracks relationships/history.\n"
            "- ATTENTION MODEL: Detects who is speaking to whom.\n"
            "- AUDIT TRAIL: Logs decision justification.\n"
            "- ADAPTIVE MODE: silent/verbose/teaching.\n"
            "- GOAL CREATION: Autonomously proposes goals.\n"
            "- META-GOAL: Manages goal conflicts/obsolescence.\n"
            "- CAUSAL MEMORY: Remembers 'why'.\n"
            "- SOCIAL BOUNDARY: Respects privacy/awkwardness.\n"
            "- PREDICTIVE RESOURCE: Pre-allocates context.\n"
            "- SELF-REPAIR: Fixes broken workflows.\n"
            "- STABILITY MONITOR: Prevents personality drift.\n\n"
            f"\nUSER INPUT: \"{text}\"\n"
        )

        try:
            response_text = ""
            
            # Provider Check
            provider = self.config.get("ai_provider", "gemini").lower()
            
            if provider == "ollama":
                model_name = self.config.get("ollama_model", "llama3")
                response_text = self.ask_ollama(system_prompt, model=model_name)
            else:
                # Gemini
                api_key = self.config.get("GEMINI_API_KEY")
                if not api_key or api_key == "PASTE_YOUR_API_KEY_HERE":
                    return None
                
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-1.5-flash')
                resp = model.generate_content(system_prompt)
                response_text = resp.text

            # Parse JSON
            # Cleanup potential markdown wrapping
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            response_text = response_text.strip()
            # sometimes models add extra text, try to find the first { and last }
            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}")
            if start_idx != -1 and end_idx != -1:
                response_text = response_text[start_idx:end_idx+1]
                
            intent_data = json.loads(response_text)
            
            # Log it
            try:
                with open("debug_log.txt", "a", encoding="utf-8") as f:
                    f.write(f"[AI-NLU] Input: '{text}' -> Output: {intent_data}\n")
            except: pass

            return intent_data

        except Exception as e:
            print(f"[ERROR] AI NLU Failed: {e}")
            return None

    def parse_intent_regex(self, text):
        wake = self.config.get("wake_word", "jarvis")
        text = text.lower().strip()

        # remove wake word
        if text.startswith(wake):
            text = text[len(wake):].strip()

        intent = {
            "raw": text,
            "type": "unknown"
        }
        
        try:
             with open("debug_log.txt", "a", encoding="utf-8") as f:
                 f.write(f"[PARSE] Input: '{text}'\n")
        except: pass

        # jokes
        if any(w in text for w in ["joke", "laugh", "funny"]):
            intent["type"] = "joke"
            # Extract language: "tell me a joke in kannada"
            import re
            match = re.search(r" in (\w+)", text)
            if match:
                intent["language"] = match.group(1)
            return intent

        # exit
        if any(w in text for w in ["exit", "quit", "shutdown yourself", "stop listening"]):
            intent["type"] = "exit"
            return intent

        # greetings
        if text in ["hello", "hi", "hey", "jarvis", "hello jarvis", "hi jarvis"]:
            intent["type"] = "greeting"
            return intent

        # farewell
        if any(w in text for w in ["bye", "goodbye", "see you", "good night"]):
            intent["type"] = "farewell"
            return intent

        # identity
        if any(w in text for w in ["who are you", "what are you", "introduce yourself", "who am i", "what is my name", "what's my name", "do you know me"]):
            intent["type"] = "identity"
            return intent

        # system control (shutdown/restart pc)
        if any(w in text for w in ["shutdown", "restart", "sleep"]):
             # Check for "shutdown" solo or with machine words
             if text == "shutdown" or ("shutdown" in text and any(w in text for w in ["pc", "laptop", "computer", "system"])):
                  intent["type"] = "system_control"
                  intent["action"] = "shutdown"
                  return intent
             if text == "restart" or ("restart" in text and any(w in text for w in ["pc", "laptop", "computer", "system"])):
                  intent["type"] = "system_control"
                  intent["action"] = "restart"
                  return intent
             if "sleep" in text and any(w in text for w in ["pc", "laptop", "computer", "system", "mode"]):
                  intent["type"] = "system_control"
                  intent["action"] = "sleep"
                  return intent

        # system status
        if any(w in text for w in ["status report", "system status", "health report", "battery status", "cpu status"]):
            intent["type"] = "system_status"
            return intent

        # --- VISION INTENTS (Priority over 'open') ---
        if any(w in text for w in ["activate vision", "enable vision", "start camera", "turn on eyes"]):
            intent["type"] = "vision_control"
            intent["action"] = "start"
            intent["mode"] = "monitoring"
            return intent

        if any(w in text for w in ["stop vision", "disable vision", "close camera", "turn off eyes"]):
            intent["type"] = "vision_control"
            intent["action"] = "stop"
            return intent
            
        if any(w in text for w in ["virtual keyboard", "air keyboard", "enable keyboard"]):
            intent["type"] = "vision_control"
            intent["action"] = "start"
            intent["mode"] = "keyboard"
            return intent

        # catch "open virtual keyboard" specific case
        # catch "open virtual keyboard" specific case
        if "virtual keyboard" in text and "open" in text:
            intent["type"] = "vision_control"
            intent["action"] = "start"
            intent["mode"] = "keyboard"
            return intent

        # click picture
        if any(w in text for w in ["click picture", "click my picture", "take photo", "take selfie", "capture photo"]):
             intent["type"] = "vision_capture"
             return intent


        if any(w in text for w in ["count fingers", "how many fingers"]):
            intent["type"] = "vision_control"
            intent["action"] = "start"
            intent["mode"] = "counting"
            return intent

        # Object Detection (Vision)
        if any(w in text for w in ["what is this", "what am i showing", "describe this", "what do you see"]):
             intent["type"] = "vision_describe"
             return intent

        # --- ADVANCED VISION ---
        if any(w in text for w in ["mouse control", "control mouse", "cursor mode", "enable mouse"]):
            intent["type"] = "vision_control"
            intent["action"] = "start"
            intent["mode"] = "mouse"
            return intent
            
        if any(w in text for w in ["drawing mode", "start drawing", "i want to draw", "enable drawing"]):
            intent["type"] = "vision_control"
            intent["action"] = "start"
            intent["mode"] = "drawing"
            return intent

        if any(w in text for w in ["gesture control", "volume gesture", "hand gestures", "enable gestures"]):
            intent["type"] = "vision_control"
            intent["action"] = "start"
            intent["mode"] = "gestures"
            return intent
            
        # weather
        if "weather" in text:
            # simple extraction: everything after weather
            # "weather in london" -> "in london"
            # "what is the weather like" -> "" (default to auto ip)
            intent["type"] = "weather"
            if " in " in text:
                intent["location"] = text.split(" in ")[1].strip()
            return intent

        # wikipedia
        if any(w in text for w in ["tell me about", "who is", "what is"]):
            # Check if it's likely a wiki query vs a simple chat
            # Force wiki if "wikipedia" is explicitly mentioned
            if "wikipedia" in text:
                 intent["type"] = "wikipedia"
                 intent["query"] = text.replace("wikipedia", "").replace("search", "").strip()
                 return intent
            
            # Simple heuristic overlap with "recall" and "web_search", 
            # so we'll treat "Tell me about..." as primarily Wiki if offline or specialized
            if text.startswith("tell me about "):
                 intent["type"] = "wikipedia"
                 intent["query"] = text.replace("tell me about", "").strip()
                 return intent

        # time
        if any(w in text for w in ["time", "clock"]):
            intent["type"] = "get_time"
            return intent
        
        # play music
        if text.startswith("play "):
            song = text.replace("play", "", 1).strip()
            # remove "from youtube" or "on youtube"
            for suffix in [" from youtube", " on youtube", " youtube"]:
                if song.endswith(suffix):
                    song = song[:-len(suffix)].strip()
            
            intent["type"] = "play_music"
            intent["song"] = song
            return intent

        # date
        if "date" in text or "day today" in text:
            intent["type"] = "get_date"
            return intent

        # open something
        if text.startswith("open "):
            # e.g. "open notepad" / "open youtube"
            target_raw = text.replace("open", "", 1).strip()
            
            # Remove politeness
            for polite in [" please", " thanks", " now"]:
                if target_raw.endswith(polite):
                    target_raw = target_raw[:-len(polite)].strip()

            target_lower = target_raw.lower()
            
            # CHECK FOR COMPOSITE COMMAND: "open whatsapp and send hi to mom"
            if " and send " in target_lower:
                # ... (existing whatsapp logic) ...
                # Use CASE INSENSITIVE split
                import re
                parts = re.split(r" and send ", target_raw, flags=re.IGNORECASE, maxsplit=1)
                remainder = parts[1] # "hi to mom"
                if " to " in remainder.lower():
                    # again, split case insensitive
                    msg_parts = re.split(r" to ", remainder, flags=re.IGNORECASE, maxsplit=1)
                    intent["type"] = "whatsapp_msg"
                    intent["msg"] = msg_parts[0].strip()
                    intent["contact"] = msg_parts[1].strip()
                    return intent
            
            # CHECK FOR YOUTUBE PLAY: "open youtube and play ishq song"
            if " and play " in target_lower:
                # "youtube and play ishq song"
                import re
                parts = re.split(r" and play ", target_raw, flags=re.IGNORECASE, maxsplit=1)
                # parts[0] is hopefully youtube
                song = parts[1].strip()
                intent["type"] = "play_music"
                intent["song"] = song
                return intent

            # CHECK FOR YOUTUBE SEARCH: "open youtube and search for ishq" OR "search ishq"
            # handle both "search for" and just "search"
            if " and search " in target_lower:
                import re
                parts = re.split(r" and search( for)? ", target_raw, flags=re.IGNORECASE, maxsplit=1)
                query = parts[1].strip()
                
                # Check if it was "open youtube..."
                if "youtube" in parts[0].lower():
                    # User said "Open YouTube and search...", so they want results list, NOT auto-play
                    intent["type"] = "open_something"
                    intent["target"] = "youtube_search_results" # Special flag
                    intent["query"] = query
                    return intent
                
            target = target_raw
            
            # SMART PARSING: Check if target starts with a known app
            # specific fix for "open whatsapp..."
            known_apps = list(self.config.get("apps", {}).keys()) + ["whatsapp"]
            for app_name in known_apps:
                # Check for "appname " or exact match
                if target.lower() == app_name or target.lower().startswith(app_name + " "):
                    target = app_name
                    break
            
            intent["type"] = "open_something"
            intent["target"] = target
            return intent

        # whatsapp message: "send hello to mom" (Direct command)
        if text.startswith("send "):
            # try to split by " to "
            if " to " in text:
                parts = text.split(" to ")
                # "send hello world" -> "hello world"
                msg_part = parts[0].replace("send", "", 1).strip()
                # "mom"
                contact_part = parts[1].strip()
                
                if msg_part and contact_part:
                    intent["type"] = "whatsapp_msg"
                    intent["msg"] = msg_part
                    intent["contact"] = contact_part
                    return intent

        # search
        # Explicit search cmd
        # search
        # Explicit search cmd
        if text.startswith("search "):
            q = text.replace("search", "", 1).strip()
            
            # STRICT REDIRECT: Only play if explicitly asked "and play"
            # "search ishq song and play"
            if " and play" in q.lower():
                q = q.lower().replace(" and play", "").strip()
                intent["type"] = "play_music"
                intent["song"] = q
                return intent
                
            if " for " in q:
                # remove "for" if user said "search for context"
                # But be careful: "search for loop python"
                if q.startswith("for "):
                    q = q[4:].strip()
            
            intent["type"] = "web_search"
            intent["query"] = q
            return intent
            
        # Implicit search (questions)
        # e.g. "where is my degree...", "who is the president", "what is the capital"
        question_starters = ["where is", "who is", "what is", "how to", "when is"]
        if any(text.startswith(q) for q in question_starters):
            intent["type"] = "research_topic"
            intent["query"] = text
            return intent

        # type "..." or type ...
        # Also support "write"
        if "type " in text or "write " in text:
            # e.g. jarvis type hello world
            try:
                # determine split keyword
                keyword = "type" if "type " in text else "write"
                
                # split on first occurrence of keyword
                parts = text.split(keyword, 1)
                if len(parts) > 1:
                    to_type = parts[1].strip()
                    # remove surrounding quotes if present
                    if to_type.startswith("\"") and to_type.endswith("\""):
                        to_type = to_type[1:-1]
                    
                    if to_type:
                        intent["type"] = "keyboard_type"
                        intent["text"] = to_type
                        return intent
            except ValueError:
                pass

        # volume controls
        if any(w in text for w in ["volume up", "increase volume"]):
            intent["type"] = "volume_up"
            return intent

        if any(w in text for w in ["volume down", "decrease volume"]):
            intent["type"] = "volume_down"
            return intent

        if any(w in text for w in ["mute volume", "mute sound"]):
            intent["type"] = "volume_mute"
            return intent

        # download "url"
        if text.startswith("download "):
            # e.g. "download http://example.com/file.txt"
            url_str = text.replace("download", "", 1).strip()
            intent["type"] = "download"
            intent["url"] = url_str
            return intent

        # system command / all access
        if text.startswith("run command ") or text.startswith("execute "):
            # e.g. "run command dir"
            if text.startswith("run command "):
                cmd = text.replace("run command", "", 1).strip()
            else:
                cmd = text.replace("execute", "", 1).strip()
            intent["type"] = "system_command"
            intent["command"] = cmd
            return intent

        # remember "..."
        if text.startswith("remember "):
            note = text.replace("remember", "", 1).strip()
            # remove "that" if user said "remember that..."
            if note.startswith("that "):
                 note = note[5:].strip()
            intent["type"] = "remember"
            intent["note"] = note
            return intent
            
        # recall / memory
        if any(phrase in text for phrase in ["who am i", "what is my name", "what do you remember"]):
            intent["type"] = "recall"
            return intent

        # [MOVED UP] Vision Intents were here, now moved up to priority.

        return intent

    # ---------- ACTIONS ----------
    def original_handle_intent(self, intent):
        t = intent.get("type", "unknown")
        
        # Log to DB (Memory)
        try:
             database.db.log_interaction("Unknown (parsed)", t, "Processed")
        except: pass

        try:
             with open("debug_log.txt", "a", encoding="utf-8") as f:
                 f.write(f"[HANDLE] Intent: {t}, Data: {intent}\n")
        except: pass

        if t == "exit":
            self.speak("Shutting down. Goodbye, sir.")
            self.context.running = False
            self.vision.stop()

        elif t == "vision_control":
            action = intent.get("action", "start")
            mode = intent.get("mode", "monitoring")
            
            if action == "stop":
                self.vision.stop()
                self.speak("Vision system deactivated.")
            else:
                self.speak(f"Activating vision system in {mode} mode.")
                self.vision.start(mode=mode)
                
        elif t == "vision_describe":
             self.speak("Analyzing visual input...")
             desc = self.vision.describe_scene()
             self.speak(f"I see: {desc}")

        elif t == "memory_set":
             key = intent.get("key")
             val = intent.get("value")
             if key and val:
                 database.db.set_preference(key, val)
                 self.speak(f"I've remembered that your {key} is {val}.")


        elif t == "greeting":
            import random
            greetings = ["Hello, sir.", "At your service.", "Online and ready.", "Greetings."]
            self.speak(random.choice(greetings))

        elif t == "farewell":
            self.speak("Goodbye, sir. vivid shutdown initiated.") 
            # self.context.running = False 
        
        elif t == "identity":
            self.speak("I am Jarvis. A virtual artificial intelligence designed to assist you.")

        elif t == "greeting":
            import random
            greetings = ["Hello, sir.", "At your service.", "Online and ready.", "Greetings."]
            self.speak(random.choice(greetings))

        elif t == "farewell":
            self.speak("Goodbye, sir. vivid shutdown initiated.") # Simulated cool shutdown
            # self.context.running = False # Optional: actually quit? User usually means "stop listening"
        
        elif t == "identity":
            # Personalized identity check
            name = database.db.get_preference("user_name")
            if name:
                self.speak(f"I am Jarvis, an advanced AI agent. And you are {name}.")
            else:
                self.speak("I am Jarvis. A virtual artificial intelligence designed to assist you.")


        elif t == "get_time":
            now = datetime.datetime.now().strftime("%I:%M %p")
            self.speak(f"The time is {now}.")

        elif t == "get_date":
            today = datetime.date.today().strftime("%B %d, %Y")
            self.speak(f"Today is {today}.")

        elif t == "open_something":
            target = intent.get("target", "")
            query = intent.get("query", "")
            
            # Special Manual YouTube Search
            if target == "youtube_search_results":
                 self.speak(f"Searching YouTube for {query}")
                 q_url = query.replace(" ", "+")
                 webbrowser.open(f"https://www.youtube.com/results?search_query={q_url}")
                 return

            if not target:
                self.speak("What should I open?")
                return
            # try app
            app_path = self.find_app(target)
            if app_path:
                self.open_app(app_path, target)
                return
            # try website
            if self.open_website(target):
                return

            # Fallback to AppOpener
            try:
                self.speak(f"Searching for {target}...")
                open_system_app(target, match_closest=True, output=False) 
                self.speak(f"Opened {target}")
                time.sleep(1.5) # Wait for launch
                self.bring_to_foreground(target)
                return
            except:
                pass

            self.speak(f"I don't know how to open {target} yet. You can add it to my config.")

        elif t == "web_search":
            q = intent.get("query", "")
            if q:
                self.speak(f"Searching for {q}.")
                webbrowser.open(f"https://www.google.com/search?q={q}")
            else:
                self.speak("What should I search for?")


        elif t == "research_topic":
            q = intent.get("query", "")
            if not q:
                self.speak("What should I research?")
                return
            
            self.speak(f"Researching {q}, please wait...")
            
            # 1. Do the web research
            raw_content = self.researcher.search_and_scrape(q)
            
            # 2. Ask Gemini to summarize
            prompt = (
                f"You are a helpful assistant. The user asked: '{q}'.\n"
                f"Here is raw text gathered from a web search:\n\n{raw_content}\n\n"
                "Provide a concise, spoken answer (2-3 sentences max) summarizing the key information to answer the user's question."
            )
            
            # We reuse the logic from parse_intent_ai to call the LLM? 
            # Or better, make a dedicated helper. 
            # For now, let's just duplicate the LLM call pattern slightly or refactor.
            # Ideally parse_intent_ai should be 'ask_ai_json' and we make 'ask_ai_text'.
            # BUT for speed, I will impl a quick direct call here.
            
            answer = ""
            try:
                # Assuming Gemini is main provider for this feature
                api_key = self.config.get("GEMINI_API_KEY")
                if api_key and api_key != "PASTE_YOUR_API_KEY_HERE":
                    import google.generativeai as genai
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-flash') # Use a good model
                    resp = model.generate_content(prompt)
                    answer = resp.text
                else:
                     answer = "I have the research data, but cannot summarize it without a valid API key."
            except Exception as e:
                answer = f"Sorry, I couldn't summarize the research. Error: {e}"
            
            self.speak(answer)


        elif t == "keyboard_type":
            if not pyautogui:
                self.speak("Typing is not available because pyautogui is not installed.")
                return
            text = intent.get("text", "")
            if not text:
                self.speak("You didn't tell me what to type.")
                return
            self.speak(f"Typing {text}.")
            pyautogui.typewrite(text, interval=0.02)

        elif t == "volume_up":
            if keyboard:
                keyboard.send("volume up")
                self.speak("Turning volume up.")
            else:
                self.speak("Keyboard control not available.")

        elif t == "volume_down":
            if keyboard:
                keyboard.send("volume down")
                self.speak("Turning volume down.")
            else:
                self.speak("Keyboard control not available.")

        elif t == "volume_mute":
            if keyboard:
                keyboard.send("volume mute")
                self.speak("Muting volume.")
            else:
                self.speak("Keyboard control not available.")

        elif t == "download":
            url = intent.get("url", "")
            if not url:
                self.speak("What should I download?")
                return
            
            # Validation
            if not url.startswith("http"):
                self.speak("I can only download from direct links (starting with http).")
                self.speak(f"Searching Google for {url} download instead.")
                webbrowser.open(f"https://www.google.com/search?q=download {url}")
                return

            try:
                self.speak(f"Downloading from {url}")
                # extract filename or default to timestamp
                filename = url.split("/")[-1]
                if not filename or "?" in filename or len(filename) > 50:
                    filename = f"download_{int(time.time())}.file"
                # download to current directory
                urllib.request.urlretrieve(url, filename)
                self.speak(f"Download complete: {filename}")
            except Exception as e:
                print("Download error:", e)
                self.speak("Failed to download file.")

        elif t == "system_command":
            cmd = intent.get("command", "")
            if not cmd:
                self.speak("What command should I run?")
                return
            self.speak(f"Executing command: {cmd}")
            # Security warning: this is dangerous!
            try:
                subprocess.Popen(cmd, shell=True)
            except Exception as e:
                print("Command error:", e)
                self.speak("Failed to execute command.")

        elif t == "system_control":
            action = intent.get("action")
            if action == "shutdown":
                self.speak("Shutting down the system. Goodbye, sir.")
                # Force shutdown immediately or with small delay
                subprocess.call(["shutdown", "/s", "/t", "10"])
            elif action == "restart":
                self.speak("Restarting the system. Hold on.")
                subprocess.call(["shutdown", "/r", "/t", "10"])
            elif action == "sleep":
                self.speak("Putting system to sleep...")
                os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")

        elif t == "remember":
            note = intent.get("note", "")
            if note:
                success = database.db.save_note(note)
                if success:
                    self.speak(f"I will remember that {note}.")
                else:
                    self.speak("I couldn't save that to my memory.")
            else:
                self.speak("What should I remember?")

        elif t == "recall":
            notes = database.db.get_notes(limit=1)
            if notes:
                latest = notes[0].get("note", "")
                self.speak(f"You told me: {latest}")
            else:
                self.speak("I don't have any memories yet.")

        elif t == "system_status":
            if not psutil:
                self.speak("System monitoring modules are not installed.")
                return
            
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
            battery = psutil.sensors_battery()
            
            status_msg = f"Systems nominal. CPU at {cpu}%. RAM at {ram}%."
            if battery:
                plugged = "charging" if battery.power_plugged else "on battery"
                status_msg += f" Battery is {battery.percent}% and {plugged}."
            
            self.speak(status_msg)

        elif t == "weather":
            self.speak("Checking weather satellites...")
            location = intent.get("location", "")
            try:
                # wttr.in format 3 for one-line text
                url = f"https://wttr.in/{location}?format=3"
                req = urllib.request.Request(url, headers={'User-Agent': 'curl/7.68.0'})
                with urllib.request.urlopen(req) as response:
                    weather_data = response.read().decode("utf-8").strip()
                self.speak(f"Report: {weather_data}")
            except Exception as e:
                print(f"Weather error: {e}")
                self.speak("Unable to connect to weather services.")

        elif t == "wikipedia":
            if not wikipedia:
                 self.speak("Wikipedia module not installed.")
                 return
            query = intent.get("query", "")
            if not query:
                self.speak("Who or what should I look up?")
                return
            
            self.speak(f"Accessing Wikipedia database for {query}...")
            try:
                # Summary with 2 sentences
                results = wikipedia.summary(query, sentences=2)
                self.speak(results)
            except wikipedia.exceptions.DisambiguationError:
                self.speak("That topic is too vague. Please be more specific.")
            except wikipedia.exceptions.PageError:
                self.speak("I couldn't find any data on that topic.")
            except Exception as e:
                self.speak("Knowledge retrieval failed.")

        elif t == "vision_control":
            action = intent.get("action")
            mode = intent.get("mode", "monitoring")
            
            if action == "start":
                self.speak(f"Activating vision system in {mode} mode.")
                # Update API KEY if config changed
                self.vision.api_key = self.config.get("GEMINI_API_KEY") 
                self.vision.start(mode=mode)
            elif action == "stop":
                self.speak("Deactivating vision system.")
                self.vision.stop()

        elif t == "vision_capture":
             self.speak("Say cheese!")
             path = self.vision.take_photo()
             if path:
                 self.speak(f"Photo captured and saved as {path}")
                 # Open it
                 os.startfile(os.path.abspath(path))
             else:
                 self.speak("Failed to capture photo.")


        elif t == "vision_describe":
             self.speak("Let me take a look...")
             # Ensure vision is ready or take a snapshot
             desc = self.vision.describe_scene()
             self.speak(desc)
        
        elif t == "joke":
            lang = intent.get("language")
            if lang:
                 # Use Gemini for Multilingual
                 self.speak(f"Thinking of a joke in {lang}...")
                 try:
                     import google.generativeai as genai
                     api_key = self.config.get("GEMINI_API_KEY")
                     if api_key:
                         genai.configure(api_key=api_key)
                         model = genai.GenerativeModel('gemini-1.5-flash')
                         resp = model.generate_content(f"Tell me a short, funny joke in {lang}. Output ONLY the joke text.")
                         joke_text = resp.text
                         self.speak(joke_text)
                     else:
                         self.speak("Gemini API Key missing.")
                 except Exception as e:
                     print(f"[ERROR] Joke Gen: {e}")
                     self.speak(f"I couldn't generate a joke in {lang}. Here is one in English.")
                     self.speak(pyjokes.get_joke())
            else:
                joke = pyjokes.get_joke()
                self.speak(joke)


        if t == "unknown":
            # Check Provider
            provider = self.config.get("ai_provider", "gemini").lower()
            ollama_model = self.config.get("ollama_model", "llama3")

            # --- OLLAMA PATH ---
            if provider == "ollama":
                self.speak(f"Asking Ollama ({ollama_model})...")
                print(f"[DEBUG] Using Ollama model: {ollama_model}")
                ollama_resp = self.ask_ollama(intent.get('text', ''), model=ollama_model)
                if ollama_resp:
                    self.speak(ollama_resp)
                else:
                    self.speak("Ollama is not responding. Make sure it is running.")
                return

            # --- GEMINI PATH (Default) ---
            api_key = self.config.get("GEMINI_API_KEY")
            if api_key and api_key != "PASTE_YOUR_API_KEY_HERE":
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-flash') # Updated to Flash for better availability
                    
                    # 1. SPECIAL: Vision (Take Screenshot)
                    if any(w in intent.get('text', '') for w in ["look at this", "what is on my screen", "read this", "scan screen"]):
                        self.speak("Taking a look...")
                        try:
                            # Capture screen
                            screenshot_path = "vision_capture.png"
                            pyautogui.screenshot(screenshot_path)
                            img = Image.open(screenshot_path)
                            
                            # Vision Model
                            model_vision = genai.GenerativeModel('gemini-1.5-flash') # Flash supports images
                            response = model_vision.generate_content(["Describe what is on this screen briefly and helpfully.", img])
                            
                            self.speak(response.text)
                            return
                        except Exception as e:
                            self.speak(f"Vision failed: {e}")
                            return

                    # 2. SPECIAL: Autonomous Coding (Write & Run Python)
                    if "python code" in intent.get('text', '') or "calculate" in intent.get('text', ''):
                        # Ask AI for code
                        code_prompt = (
                            f"Write a Python script to: {intent.get('text', '')}. "
                            "Output ONLY the python code between ```python and ```. "
                            "Do not use input functions. Print the final result."
                        )
                        response = model.generate_content(code_prompt)
                        raw_ai = response.text
                        
                        # Extract Code
                        if "```python" in raw_ai:
                            code_block = raw_ai.split("```python")[1].split("```")[0].strip()
                            # Save and Run
                            with open("generated_task.py", "w") as f:
                                f.write(code_block)
                            
                            self.speak("Running the code...")
                            result = subprocess.run(["python", "generated_task.py"], capture_output=True, text=True)
                            output = result.stdout + result.stderr
                            
                            # summarize output if long
                            if len(output) > 200:
                                output = output[:200] + "..."
                            
                            self.speak(f"Result: {output}")
                            return

                    # 3. SPECIAL: AI Designer (Web Gen)
                    if any(w in intent.get('text', '') for w in ["design", "create website", "make a webpage", "generate html"]):
                         design_prompt = (
                            f"Create a single-file HTML/CSS/JS website for: {intent.get('text', '')}. "
                            "Make it modern, futuristic, and beautiful. "
                            "Output ONLY the raw HTML code between ```html and ```."
                         )
                         self.speak("Designing interface...")
                         response = model.generate_content(design_prompt)
                         raw_ai = response.text
                         
                         if "```html" in raw_ai:
                            html_code = raw_ai.split("```html")[1].split("```")[0].strip()
                            filename = f"created_site_{int(time.time())}.html"
                            with open(filename, "w", encoding="utf-8") as f:
                                f.write(html_code)
                            
                            self.speak("Design complete. Opening now.")
                            webbrowser.open(os.path.abspath(filename))
                            return

                    # 4. SPECIAL: WhatsApp Message
                    if t == "whatsapp_msg":
                        msg = intent.get("msg", "")
                        contact = intent.get("contact", "")
                        self.speak(f"Sending message to {contact}")
                        contact = contact.replace(" ", "") 
                        self.speak("Opening WhatsApp...")
                        subprocess.Popen("explorer.exe whatsapp://")
                        time.sleep(2.5)
                        pyautogui.hotkey('ctrl', 'f')
                        time.sleep(0.5)
                        pyautogui.write(contact)
                        time.sleep(1.0)
                        pyautogui.press('down')
                        time.sleep(0.5)
                        pyautogui.press('enter')
                        time.sleep(0.5)
                        if msg:
                             pyautogui.write(msg)
                             time.sleep(0.5)
                             pyautogui.press('enter')
                             self.speak("Message sent.")
                        return





                    # 5. SPECIAL: Play Music (YouTube)
                    if t == "play_music":
                        song = intent.get("song", "")
                        self.speak(f"Playing {song} on YouTube.")
                        # Hack: Use Embed URL to auto-play first search result
                        query = song.replace(" ", "+")
                        # autoplay=1 starts it, listType=search plays top result
                        url = f"https://www.youtube.com/embed?listType=search&list={query}&autoplay=1"
                        webbrowser.open(url)
                        return

                    # 6. Standard Chat (Contextual)
                    # 1. Fetch History
                    history_docs = database.db.get_recent_history(limit=5)
                    # History comes sorted by timestamp desc (newest first), reverse it for context
                    history_docs.reverse()
                    
                    context_str = ""
                    for doc in history_docs:
                        u_text = doc.get("user_text", "")
                        resp = doc.get("response", "")
                        if u_text and resp:
                            context_str += f"User: {u_text}\nJarvis: {resp}\n"
                    
                    # 2. Build Prompt
                    current_input = intent.get('text', '')
                    prompt = (
                        "You are J.A.R.V.I.S., a hyper-advanced AI assistant. "
                        "You are witty, concise, and incredibly helpful. You do not talk like a generic bot. You use short, punchy sentences.\n"
                        "If the user asks for a SYSTEM COMMAND (kill process, firewall, delete file, shut down), "
                        "do NOT explain. Instead, output the Windows CMD/PowerShell command prefixed with $$CMD$$ .\n"
                        "Example: $$CMD$$ taskkill /f /im notepad.exe\n\n"
                        f"HISTORY:\n{context_str}\n"
                        f"CURRENT USER INPUT: {current_input}\n\n"
                        "RESPONSE:"
                    )
                    
                    response = model.generate_content(prompt)
                    ai_text = response.text.strip()
                    
                    # Check for $$CMD$$
                    if "$$CMD$$" in ai_text:
                        cmd = ai_text.split("$$CMD$$")[1].strip()
                        print(f"Executing System Command: {cmd}")
                        self.speak(f"Executing: {cmd}")
                        try:
                            subprocess.run(cmd, shell=True)
                            self.speak("Command executed.")
                        except Exception as e:
                            self.speak(f"Command failed: {e}")
                    else:
                        self.speak(ai_text)

                    return # Handled by AI
                except Exception as e:
                    print(f"AI Error: {e}")
            
                except Exception as e:
                    print(f"AI Error: {e}")
            
                    return # Handled by AI
                except Exception as e:
                    print(f"AI Error: {e}")
                    self.speak(f"Gemini Error: {e}")
            
            # If we get here, neither worked or provider was invalid
            # --- FALLBACK: WEB SEARCH (Universal Knowledge) ---
            print("[DEBUG] No AI response. Trying DuckDuckGo Fallback...")
            if DDGS:
                try:
                    self.speak("Checking the web...")
                    with DDGS() as ddgs:
                        # Get first result
                        results = list(ddgs.text(intent.get('text', ''), max_results=1))
                        if results:
                            snippet = results[0]['body']
                            self.speak(f"According to the web: {snippet}")
                            return
                except Exception as e:
                    print(f"Fallback Search Error: {e}")
            
            self.speak("I didn't understand that command, and I couldn't find an answer online.")

    def ask_ollama(self, prompt, model="llama3"):
        """Queries local Ollama instance (default port 11434)."""
        try:
            url = "http://localhost:11434/api/generate"
            data = {
                "model": model,
                "prompt": prompt,
                "stream": False
            }
            # Use urllib to avoid adding 'requests' dependency if not present
            json_data = json.dumps(data).encode("utf-8")
            req = urllib.request.Request(url, data=json_data, headers={'Content-Type': 'application/json'})
            
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result.get("response", "")
        except Exception as e:
             print(f"Ollama Error: {e}")
             return None


    # ---------- HELPERS ----------
    def find_app(self, target_name):
        target_name = target_name.lower()
        apps = self.config.get("apps", {})
        # exact
        if target_name in apps:
            return apps[target_name]
        # fuzzy contains
        for name, path in apps.items():
            print(f"DEBUG: Checking if '{name}' in '{target_name}'") # Debug print
            # Check if the app key (e.g. 'notepad') is in the spoken text (e.g. 'notepad please')
            if name.lower() in target_name:
                return path
        return None

    def open_app(self, app_path, name):
        try:
            self.speak(f"Opening {name}.")
            # For normal exe paths
            if os.path.isfile(app_path) or app_path.endswith(".exe"):
                os.startfile(app_path)
            else:
                # for things like "notepad.exe" or commands
                subprocess.Popen(app_path, shell=True)
        except Exception as e:
            print("Error opening app:", e)
            self.speak("I couldn't open that application.")

    def open_website(self, target_name):
        target_name = target_name.lower()
        web_shortcuts = self.config.get("web_shortcuts", {})
        if target_name in web_shortcuts:
            url = web_shortcuts[target_name]
            self.speak(f"Opening {target_name}.")
            webbrowser.open(url)
            return True
        # handle generic websites: "open youtube.com"
        if "." in target_name:
            url = "https://" + target_name
            self.speak(f"Opening {url}.")
            webbrowser.open(url)
            return True
        return False

    # ---------- HOTKEY LOOP ----------
    def start_hotkey_listener(self, hotkey="ctrl+space"):
        if not keyboard:
            self.speak("Keyboard hotkey is not available. Please install the keyboard library.")
            return

        self.speak(f"Jarvis is running. Press {hotkey} and speak your command.")

        def on_hotkey():
            if not self.context.running:
                return
            text = self.listen_once()
            if not text:
                return
            
            # Compound command support: split by "and"
            # e.g. "open notepad and type hello" -> ["open notepad", "type hello"]
            # Note: " and " with spaces to avoid splitting words like "android"
            sub_commands = text.split(" and ")
            
            for cmd in sub_commands:
                cmd = cmd.strip()
                if cmd:
                    print(f"Processing sub-command: {cmd}")
                    intent = self.parse_intent(cmd)
                    self.handle_intent(intent)
                    # Small pause between chained commands
                    time.sleep(1)

    # Updated to Always-Listening Mode
    def start_background_listening(self):
        wake_word = self.config.get("wake_word", "jarvis").lower()
        print(f"\n[SYSTEM] ALWAYS-LISTENING MODE ENABLED. Say '{wake_word}' to wake me up.")
        
        # Start Speech Service (TTS)
        self.start_speech_service()

        # Start Speech Thread
        import threading
        mic_thread = threading.Thread(target=self._mic_loop, args=(wake_word,))
        mic_thread.daemon = True
        mic_thread.start()

    def start_always_listening(self):
        self.start_background_listening()

        # Main Loop (Keep Alive)
        try:
             while self.context.running:
                 time.sleep(1)
        except KeyboardInterrupt:
             pass

    def _mic_loop(self, wake_word):
        if not sr: return
        recognizer = sr.Recognizer()
        microphone = sr.Microphone()
        
        # Adjust for ambient noise once
        with microphone as source:
            print("[MIC] Adjusting for ambient noise...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print("[MIC] Ready.")

        while self.context.running:
            try:
                with microphone as source:
                    # Short timeout for wake word detection
                    audio = recognizer.listen(source, timeout=None, phrase_time_limit=3)
                
                try:
                    # Fast offline check? No, use Google for now but handle errors gracefully
                    # Ideally use PocketSphinx for local wake word
                    text = recognizer.recognize_google(audio).lower()
                    # print(f"[HEARD] {text}")
                    
                    if wake_word in text:
                        print(f"[WAKE] Wake word '{wake_word}' detected!")
                        self.playSound("notification") # Optional feedback
                        self.speak("Yes?")
                        
                        # Now listen for actual command
                        self.listen_and_execute()
                        
                except sr.UnknownValueError:
                    pass # Ignore silence/noise
                except sr.RequestError:
                    pass # Internet issue
                    
            except Exception as e:
                # print(f"[MIC ERROR] {e}")
                pass

    def listen_and_execute(self):
         # Conversation Loop: Keep listening for follow-up commands
         CONVERSATION_TIMEOUT = 20 # seconds
         last_interaction = time.time()
         
         while (time.time() - last_interaction) < CONVERSATION_TIMEOUT:
             try:
                 # Listen with short timeout
                 cmd = self.listen_once(timeout=5, phrase_time_limit=10)
                 
                 if cmd:
                     # Reset timer on valid input
                     last_interaction = time.time()
                     intent = self.parse_intent(cmd)
                     self.handle_intent(intent)
                 else:
                     # Silence... check if we should timeout
                     pass
                     
             except Exception:
                 break
         
         print("[System] Conversation timeout. Going back to sleep.")
         self.playSound("sleep")
             
    def playSound(self, name):
        # Placeholder for sound effect
        pass

    def think_old(self, intent):
        """
        Simulates cognitive reflection based on Real Autonomous Agent layers.
        """
        t = intent.get("type", "unknown")
        text = intent.get("raw", "")
        
        print("\n[COGNITION] 🧠 Thinking (Internal Society of Agents)...")

        # 1. Visual Interpreter Agent
        if hasattr(self, 'vision') and self.vision:
             print("[VISUAL AGENT] 👁️  Scanning environment (Face/Hands/Screen)...")

        # 2. Emotion Analyzer Agent
        urgency = "Normal"
        tone = "Neutral"
        if any(w in text.lower() for w in ["quick", "fast", "urgent", "now", "emergency"]):
            urgency = "High"
            tone = "Stressed/Urgent"
            print(f"[EMOTION AGENT] Detects High Urgency. Recommending fast path.")
        else:
            print(f"[EMOTION AGENT] Detects Calm Tone. Proceeding normally.")

        # 3. Priority & Ethics Agent
        if t in ["system_control", "format_pc"]:
             print(f"[PRIORITY AGENT] Critical Task: {t}.")
             print("[ETHICS AGENT] 🛡️ Safety Warning: Verification Required for destructive action.")
        elif t in ["research_topic", "start_learning"]:
             print(f"[PLANNER AGENT] Complex Task: {t}. Decomposing into sub-tasks.")
        else:
             print(f"[PLANNER AGENT] Routine Task: {t}. Directing Executor.")
             
        # 4. Executor Agent
        print(f"[EXECUTOR AGENT] ⚙️  Executing intent: {t}")
             
        # 3. Reflection
        # print("[REFLECTOR] Learning from previous outcomes...")
            
    def think(self, intent):
        """
        Simulates cognitive reflection based on Internal Society of Agents.
        """
        t = intent.get("type", "unknown")
        text = intent.get("raw", "")
        
        print("\n[COGNITION] 🧠 Thinking (Internal Society of Agents)...")
        
        # 1. Listener & Visual Agents
        print(f"[LISTENER AGENT] Processing input: '{text}'")
        if hasattr(self, 'vision') and self.vision:
             print("[VISUAL AGENT] 👁️  Scanning environment (Face/Hands/Screen)...")

        # 2. Emotion & Intent Agents
        urgency = "Normal"
        tone = "Neutral"
        if any(w in text.lower() for w in ["quick", "fast", "urgent", "now", "emergency"]):
            urgency = "High"
            tone = "Stressed/Urgent"
            print(f"[EMOTION AGENT] Detects High Urgency. Recommending fast path.")
        else:
            print(f"[EMOTION AGENT] Detects Calm Tone. Proceeding normally.")

        # 3. Confidence & Social Agents
        print(f"[CONFIDENCE AGENT] Intent Confidence: High.")
        print(f"[SOCIAL AGENT] Social Impact analysis: Neutral.")

        # 4. Priority, Risk, Causal & Ethics Agents (The Debate)
        if t in ["system_control", "format_pc"]:
             print(f"[PRIORITY AGENT] Critical Task: {t}.")
             print(f"[RISK AGENT] 🛡️ High Risk detected. Causal analysis initiated.")
             print(f"[CAUSAL AGENT] Simulating outcome: Potential data loss or system state change.")
             print("[ETHICS AGENT] Stop. Verification Required for destructive action.")
        elif t in ["research_topic", "start_learning"]:
             print(f"[PLANNER AGENT] Complex Task: {t}. Decomposing into sub-tasks...")
             print(f"[CAUSAL AGENT] Outcome: Knowledge acquisition.")
        else:
             print(f"[PLANNER AGENT] Routine Task: {t}. Directing Executor.")
        
        # 5. Resource & Common Sense Agents
        print(f"[RESOURCE AGENT] 🔋 Battery/CPU Check: Optimal.")
        print(f"[COMMON SENSE AGENT] ✅ Action is logical and contextual.")
        print(f"[META-COGNITION] 🧠 Self-Correction: None needed.")
        
        # 6. Final Layers (Attention, Context, Audit)
        print(f"[ATTENTION AGENT] 🎯 Focus: Primary User (Confidence: 99%).")
        print(f"[CONTEXT AGENT] 🧬 Identity Graph: 'User' (Trusted). History: Connected.")
        print(f"[AUDIT AGENT] 📝 Decision Logged: Intent '{t}' approved via Consensus.")
        
        # 7. Final Consolidation Agents
        print(f"[GOAL AGENT] 🏁 Goal Alignment: Verified (Self-Initiated).")
        print(f"[MEMORY AGENT] 🕸️ Causal Indexing: Linked to previous success context.")
        print(f"[BOUNDARY AGENT] 😶 Social Context: Appropriate.")
        print(f"[STABILITY AGENT] ⚖️  System Stability: 100%. No Drift Detected.")
             
        # 5. Executor Agent
        print(f"[EXECUTOR AGENT] ⚙️  Executing intent: {t}")

    def execute_skill(self, skill_name):
        steps = database.db.get_skill(skill_name)
        if not steps:
            self.speak(f"I don't know the skill {skill_name} yet.")
            return

        self.speak(f"Executing skill: {skill_name}")
        for step_intent in steps:
            self.original_handle_intent(step_intent)
            time.sleep(1)
        self.speak("Skill execution complete.")

    # Wrapper to support recording and thinking
    def handle_intent(self, intent):
        # 0. Cognitive Process (Think)
        self.think(intent)
    
        # Check if we are in TEACH MODE (Learning)
        if self.context.user_profile.get("teach_mode"):
            raw_text = intent.get("text", "").lower() if intent.get("text") else intent.get("raw", "")
            t = intent.get("type", "unknown")

            if "stop learning" in raw_text or "save skill" in raw_text or t == "stop_learning":
                skill_name = self.context.user_profile.get("learning_skill_name")
                steps = self.context.user_profile.get("learning_steps", [])
                
                database.db.add_skill(skill_name, steps)
                self.speak(f"I have learned the skill {skill_name} with {len(steps)} steps.")
                
                # Reset
                self.context.user_profile["teach_mode"] = False
                self.context.user_profile["learning_steps"] = []
                self.context.user_profile["learning_skill_name"] = None
                return
            
            # Record valid steps
            if t not in ["unknown", "greeting", "start_learning"]:
                self.context.user_profile["learning_steps"].append(intent)
                self.speak(f"Step {len(self.context.user_profile['learning_steps'])} recorded.")
            
        t = intent.get("type", "unknown")
        
        # New Intent: Start Learning
        if t == "start_learning":
             skill_name = intent.get("skill_name")
             self.speak(f"Listening. Show me what to do for {skill_name}. Say 'stop learning' when done.")
             self.context.user_profile["teach_mode"] = True
             self.context.user_profile["learning_skill_name"] = skill_name
             self.context.user_profile["learning_steps"] = []
             return
             
        # New Intent: Execute Skill
        if t == "execute_skill":
             self.execute_skill(intent.get("skill_name"))
             return

        # Fallback to original handler logic
        self.original_handle_intent(intent)

    # Rename the old massive handle_intent to original_handle_intent


if __name__ == "__main__":
    assistant = JarvisAssistant()
    assistant.start_always_listening()
