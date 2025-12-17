"""
This file contains a collection of tools that the Jarvis assistant can use to perform various actions.
Each function is a "tool" that can be called by the AI agent to interact with the system,
access information, or control applications.
"""
import datetime
import webbrowser
import os
import subprocess
import time
import psutil
import wikipedia
import pyjokes
import pyautogui
import keyboard
import requests
from AppOpener import open as open_system_app
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import database

# --- Helper Classes & Functions ---

class WebResearcher:
    def __init__(self):
        self.driver = None

    def _setup_driver(self):
        if not self.driver:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--log-level=3")
            try:
                self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
            except Exception as e:
                print(f"[ERROR] Failed to setup Selenium Driver: {e}")
                self.driver = None

    def search_and_scrape(self, query):
        self._setup_driver()
        if not self.driver:
            return "Web research capabilities are currently unavailable."
        try:
            self.driver.get(f"https://www.google.com/search?q={query}")
            time.sleep(2)
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            for script in soup(["script", "style"]):
                script.extract()
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            clean_text = '\n'.join(chunk for chunk in chunks if chunk)
            return clean_text[:8000]
        except Exception as e:
            return f"Error during research: {e}"

# --- Tool Functions ---

def get_current_time() -> str:
    """Returns the current time in HH:MM AM/PM format."""
    return datetime.datetime.now().strftime("%I:%M %p")

def get_current_date() -> str:
    """Returns the current date in Month Day, Year format."""
    return datetime.date.today().strftime("%B %d, %Y")

def open_application_or_website(target: str, config: dict) -> str:
    """
    Opens a specified application or website.
    """
    apps = config.get("apps", {})
    web_shortcuts = config.get("web_shortcuts", {})
    target_lower = target.lower()

    if target_lower in apps:
        os.startfile(apps[target_lower])
        return f"Opened application: {target}"
    elif target_lower in web_shortcuts:
        webbrowser.open(web_shortcuts[target_lower])
        return f"Opened website: {target}"
    elif "." in target_lower:
        webbrowser.open("https://" + target_lower)
        return f"Opened website: {target}"
    else:
        try:
            open_system_app(target, match_closest=True, output=False)
            return f"Opened system application: {target}"
        except Exception:
            return f"Could not open {target}."

def search_web(query: str) -> str:
    """Searches the web for a given query and opens the results in a browser."""
    webbrowser.open(f"https://www.google.com/search?q={query}")
    return f"Searching for {query} on Google."

def research_topic(query: str, llm_summarizer) -> str:
    """
    Performs in-depth research on a topic by scraping web results and using an LLM to generate a summary.
    """
    researcher = WebResearcher()
    raw_content = researcher.search_and_scrape(query)
    prompt = (
        f"You are a helpful assistant. The user asked: '{query}'.\n"
        f"Here is raw text gathered from a web search:\n\n{raw_content}\n\n"
        "Provide a concise, spoken answer (2-3 sentences max) summarizing the key information to answer the user's question."
    )
    return llm_summarizer(prompt)

def type_text(text: str) -> str:
    """Types the given text using the keyboard."""
    pyautogui.typewrite(text, interval=0.02)
    return f"Typed: {text}"

def control_system_volume(direction: str) -> str:
    """Controls the system volume. Direction can be 'up', 'down', or 'mute'."""
    if direction not in ["up", "down", "mute"]:
        return "Invalid volume direction."
    keyboard.send(f"volume {direction}")
    return f"Volume set to {direction}."

def download_file(url: str) -> str:
    """Downloads a file from a given URL."""
    if not url.startswith("http"):
        return "Invalid URL. Must start with http or https."
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        filename = url.split("/")[-1] or f"download_{int(time.time())}.file"
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return f"Downloaded {filename}."
    except requests.exceptions.RequestException as e:
        return f"Failed to download file: {e}"

def execute_system_command(command: str) -> str:
    """Executes a system command in the shell."""
    try:
        subprocess.Popen(command, shell=True)
        return f"Executing command: {command}"
    except Exception as e:
        return f"Failed to execute command: {e}"

def control_system_power(action: str) -> str:
    """Controls the system's power state. Action can be 'shutdown', 'restart', or 'sleep'."""
    if action == "shutdown":
        subprocess.call(["shutdown", "/s", "/t", "10"])
        return "Shutting down the system."
    elif action == "restart":
        subprocess.call(["shutdown", "/r", "/t", "10"])
        return "Restarting the system."
    elif action == "sleep":
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
        return "Putting the system to sleep."
    return "Invalid power action."

def save_note(note: str) -> str:
    """Saves a note to the database."""
    if database.db.save_note(note):
        return f"I will remember that: {note}"
    return "Could not save the note."

def get_notes() -> str:
    """Retrieves the most recent note from the database."""
    notes = database.db.get_notes(limit=1)
    if notes:
        return f"You told me: {notes[0].get('note', '')}"
    return "I don't have any memories yet."

def get_system_status() -> str:
    """Returns the current system status (CPU, RAM, Battery)."""
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    battery = psutil.sensors_battery()
    status_msg = f"Systems nominal. CPU at {cpu}%. RAM at {ram}%."
    if battery:
        plugged = "charging" if battery.power_plugged else "on battery"
        status_msg += f" Battery is {battery.percent}% and {plugged}."
    return status_msg

def get_weather(location: str = "") -> str:
    """Gets the weather for a given location."""
    try:
        response = requests.get(f"https://wttr.in/{location}?format=3", headers={'User-Agent': 'curl/7.68.0'})
        response.raise_for_status()
        return f"Weather Report: {response.text.strip()}"
    except requests.exceptions.RequestException as e:
        return f"Unable to connect to weather services: {e}"

def search_wikipedia(query: str) -> str:
    """Searches Wikipedia for a query and returns a summary."""
    try:
        return wikipedia.summary(query, sentences=2)
    except wikipedia.exceptions.DisambiguationError:
        return "That topic is too vague. Please be more specific."
    except wikipedia.exceptions.PageError:
        return "I couldn't find any data on that topic."
    except Exception:
        return "Knowledge retrieval failed."

def control_vision_system(vision_system, action: str, mode: str = "monitoring") -> str:
    """Controls the vision system. Action can be 'start' or 'stop'."""
    if action == "start":
        vision_system.start(mode=mode)
        return f"Vision system started in {mode} mode."
    elif action == "stop":
        vision_system.stop()
        return "Vision system stopped."
    return "Invalid vision action."

def capture_photo(vision_system) -> str:
    """Captures a photo using the vision system."""
    path = vision_system.take_photo()
    if path:
        os.startfile(os.path.abspath(path))
        return f"Photo captured and saved as {path}"
    return "Failed to capture photo."

def describe_scene(vision_system) -> str:
    """Describes the current scene using the vision system's camera."""
    return vision_system.describe_scene()

def tell_joke(language: str = "en", llm_joke_generator=None) -> str:
    """Tells a joke, either in English or another specified language using an LLM."""
    if language != "en" and llm_joke_generator:
        try:
            return llm_joke_generator(f"Tell me a short, funny joke in {language}. Output ONLY the joke text.")
        except Exception:
            return f"I couldn't generate a joke in {language}. Here is one in English: {pyjokes.get_joke()}"
    return pyjokes.get_joke()

def send_whatsapp_message(contact: str, message: str) -> str:
    """Sends a WhatsApp message to a specified contact."""
    contact = contact.replace(" ", "")
    subprocess.Popen(f"explorer.exe whatsapp://send?phone={contact}&text={message.replace(' ', '%20')}")
    time.sleep(2)
    pyautogui.press('enter')
    return f"Sent '{message}' to {contact} on WhatsApp."

def play_music_on_youtube(song_name: str) -> str:
    """Searches for and plays a song on YouTube."""
    query = song_name.replace(" ", "+")
    url = f"https://www.youtube.com/embed?listType=search&list={query}&autoplay=1"
    webbrowser.open(url)
    return f"Playing {song_name} on YouTube."
