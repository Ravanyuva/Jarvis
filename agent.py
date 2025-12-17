"""
This file defines the Agent, the core reasoning engine for the Jarvis assistant.
The Agent uses a large language model to understand user commands, select the appropriate tools,
and execute them to fulfill the user's request, with safety checks for dangerous actions.
"""
import json
import inspect
import tools
import google.generativeai as genai
import requests

class Agent:
    DANGEROUS_TOOLS = ["execute_system_command", "control_system_power"]

    def __init__(self, assistant):
        self.assistant = assistant
        self.llm_provider = assistant.config.get("ai_provider", "gemini").lower()
        self.tools = self._discover_tools()
        self.model = self._configure_llm()

    def _discover_tools(self):
        """Discovers available tools from the tools module."""
        return {name: func for name, func in inspect.getmembers(tools, inspect.isfunction) if not name.startswith("_")}

    def _configure_llm(self):
        """Configures the generative model based on the provider."""
        if self.llm_provider == "gemini":
            api_key = self.assistant.config.get("GEMINI_API_KEY")
            if not api_key or api_key == "PASTE_YOUR_API_KEY_HERE":
                raise ValueError("Gemini API key is not configured.")
            genai.configure(api_key=api_key)
            return genai.GenerativeModel("gemini-1.5-flash", generation_config={"temperature": 0.3})
        elif self.llm_provider == "ollama":
            return self.assistant.config.get("ollama_model", "llama3")
        return None

    def _get_tool_definitions(self):
        """Returns a formatted string of tool definitions for the LLM prompt."""
        return "\n".join(
            f"- `{name}({', '.join(inspect.signature(func).parameters.keys())})`: {inspect.getdoc(func) or ''}"
            for name, func in self.tools.items()
        )

    def think(self, user_command: str) -> (str, dict):
        """Uses the LLM to determine the appropriate tool and arguments for a command."""
        system_prompt = (
            "You are Jarvis, a helpful AI assistant. Select the single best tool to accomplish the user's goal "
            "and respond with a single, valid JSON object containing 'tool_name' and 'arguments'.\n\n"
            "Available Tools:\n"
            f"{self._get_tool_definitions()}\n\n"
            "User: 'What's the weather like in London?'\n"
            "Response: {\"tool_name\": \"get_weather\", \"arguments\": {\"location\": \"London\"}}"
        )
        full_prompt = f"{system_prompt}\n\nUser: '{user_command}'\nResponse:"

        try:
            if self.llm_provider == "gemini":
                response = self.model.generate_content(full_prompt)
                response_text = response.text.strip()
            elif self.llm_provider == "ollama":
                response_text = self._ask_ollama(full_prompt, model=self.model)

            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]

            parsed = json.loads(response_text)
            return parsed.get("tool_name"), parsed.get("arguments", {})
        except Exception as e:
            print(f"[ERROR] Agent thinking failed: {e}")
            return None, None

    def _ask_ollama(self, prompt, model="llama3"):
        """Queries the local Ollama instance."""
        try:
            r = requests.post("http://localhost:11434/api/generate", json={"model": model, "prompt": prompt, "stream": False})
            r.raise_for_status()
            return r.json().get("response", "")
        except requests.exceptions.RequestException as e:
            print(f"Ollama Error: {e}")
            return None

    def execute(self, user_command: str) -> str:
        """Executes a command after performing safety checks."""
        tool_name, arguments = self.think(user_command)

        if not tool_name or tool_name not in self.tools:
            return "I'm not sure how to do that. Could you please rephrase?"

        if tool_name in self.DANGEROUS_TOOLS:
            self.assistant.speak(f"Are you sure you want me to run the command: {tool_name} with parameters {arguments}? Please say 'yes' to confirm.")
            confirmation = self.assistant.listen_once(timeout=10)
            if "yes" not in confirmation.lower():
                return "Command cancelled."

        return self._execute_tool(tool_name, arguments)

    def _execute_tool(self, tool_name: str, arguments: dict) -> str:
        """Executes the selected tool with the given arguments."""
        tool_function = self.tools[tool_name]

        # Dependency injection
        if "config" in inspect.signature(tool_function).parameters:
            arguments["config"] = self.assistant.config
        if "vision_system" in inspect.signature(tool_function).parameters:
            arguments["vision_system"] = self.assistant.vision
        if any(p in inspect.signature(tool_function).parameters for p in ["llm_summarizer", "llm_joke_generator"]):
            llm_func = (lambda p: self.model.generate_content(p).text) if self.llm_provider == "gemini" else (lambda p: self._ask_ollama(p, model=self.model))
            arguments.update({"llm_summarizer": llm_func, "llm_joke_generator": llm_func})

        try:
            return tool_function(**arguments)
        except TypeError as e:
            return f"Argument mismatch for tool '{tool_name}': {e}"
        except Exception as e:
            return f"An error occurred while executing '{tool_name}': {e}"
