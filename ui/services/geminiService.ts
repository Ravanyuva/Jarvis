import { GoogleGenAI, Type, FunctionDeclaration } from "@google/genai";

// --- TYPES ---
interface ToolCall {
  name: string;
  args: {
    action: string;
    target: string;
  };
}

interface AIResponse {
  text: string;
  toolCalls?: ToolCall[];
  source: 'OLLAMA' | 'GEMINI' | 'OFFLINE';
}

// --- CONFIG ---
const langMap: Record<string, string> = {
  'en-US': 'English (US)',
  'en-GB': 'English (UK)',
  'en-IN': 'English (India)',
  'hi-IN': 'Hindi',
  'kn-IN': 'Kannada',
  'ta-IN': 'Tamil',
  'te-IN': 'Telugu',
  'ml-IN': 'Malayalam',
  'ja-JP': 'Japanese',
  'zh-CN': 'Chinese (Simplified)'
};

// --- GEMINI TOOLS ---
const executeTaskFunction: FunctionDeclaration = {
  name: 'executeSystemTask',
  parameters: {
    type: Type.OBJECT,
    description: 'Execute a command on the user\'s interface.',
    properties: {
      action: { type: Type.STRING, description: 'Action: "open", "search", "system", "type", "security", "file_system", "process_control", "quantum", "email", "whatsapp", "media", "notification", "python_script".' },
      target: { type: Type.STRING, description: 'Target details. For whatsapp: "Contact Name:Message". For media: "Song Name". For file_system: "create_folder:FolderName". For python_script: "script.py".' },
    },
    required: ['action', 'target'],
  },
};

export class GeminiService {
  private ai: GoogleGenAI;
  private model: string = "gemini-2.5-flash";
  private ollamaUrl = "http://localhost:11434/api/chat";

  constructor() {
    this.ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
  }

  // --- MAIN ENTRY POINT ---
  async sendMessage(
    history: { role: string; parts: { text: string }[] }[],
    newMessage: string,
    language: string = 'en-US',
    isQuantumMode: boolean = false
  ): Promise<AIResponse> {
    
    // 1. Try OLLAMA (Local Llama 3) First
    try {
      const ollamaResponse = await this.callOllama(history, newMessage, language, isQuantumMode);
      if (ollamaResponse) return ollamaResponse;
    } catch (e) {
      console.log("Ollama unreachable, falling back to Gemini.");
    }

    // 2. Try GEMINI (Cloud)
    try {
      return await this.callGemini(history, newMessage, language, isQuantumMode);
    } catch (error: any) {
      console.error("Gemini Error:", error);
      
      // 3. Fallback to OFFLINE if Quota exceeded or network error
      if (
        error.status === 429 || 
        error.message?.includes('429') || 
        error.message?.toLowerCase().includes('quota') || 
        error.message?.includes('resource_exhausted') ||
        error.message?.includes('fetch')
      ) {
        console.warn("Quota exceeded. Switching to Offline Mode.");
        return this.getOfflineResponse(newMessage);
      }
      
      return { text: "Protocol Failure. Neural Link Severed.", source: 'OFFLINE' };
    }
  }

  // --- OLLAMA IMPLEMENTATION ---
  private async callOllama(
    history: { role: string; parts: { text: string }[] }[], 
    newMessage: string, 
    language: string, 
    isQuantumMode: boolean
  ): Promise<AIResponse | null> {
    
    const fullLangName = langMap[language] || language;
    const identity = isQuantumMode ? "You are YUVA PRIME. God-like, concise, omnipotent." : "You are YUVA. Helpful, witty, efficient assistant.";
    
    const systemPrompt = `
      ${identity}
      Current Language: ${fullLangName}. Reply in ${fullLangName} script.
      Pronounce name as: "You-vah".
      
      CAPABILITIES:
      You can control the system. To perform an action, you MUST output a JSON block at the end of your response.
      Format:
      ___JSON_START___
      { "name": "executeSystemTask", "args": { "action": "ACTION_NAME", "target": "TARGET_VALUE" } }
      ___JSON_END___

      Actions:
      - open (apps/websites)
      - search (google query)
      - system (lock, screenshot, downloads, shutdown, restart)
      - whatsapp (contact:message)
      - media (play song)
      - email (compose)
      - quantum (quantum_engage)
      - notification (reminders/alerts)
      - python_script (run script_name.py)
      - file_system (create_folder:Name)
    `;

    // Convert history to Ollama format
    const messages = history.map(h => ({
      role: h.role === 'model' ? 'assistant' : 'user',
      content: h.parts[0].text
    }));
    messages.push({ role: 'system', content: systemPrompt });
    messages.push({ role: 'user', content: newMessage });

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 3000); 

      const check = await fetch(this.ollamaUrl.replace('/chat', '/tags'), { method: 'GET', signal: controller.signal });
      clearTimeout(timeoutId);
      
      if (!check.ok) return null; 

      const response = await fetch(this.ollamaUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: 'llama3', 
          messages: messages,
          stream: false
        })
      });

      if (!response.ok) return null;

      const data = await response.json();
      const rawText: string = data.message.content;

      let cleanText = rawText;
      const toolCalls: ToolCall[] = [];

      const jsonMatch = rawText.match(/___JSON_START___([\s\S]*?)___JSON_END___/);
      if (jsonMatch && jsonMatch[1]) {
        try {
          const tool = JSON.parse(jsonMatch[1]);
          toolCalls.push(tool);
          cleanText = rawText.replace(jsonMatch[0], '').trim();
        } catch (e) {
          console.error("Failed to parse Ollama JSON tool", e);
        }
      }

      return {
        text: cleanText,
        toolCalls: toolCalls.length > 0 ? toolCalls : undefined,
        source: 'OLLAMA'
      };

    } catch (e) {
      return null;
    }
  }

  // --- GEMINI IMPLEMENTATION ---
  private async callGemini(
    history: { role: string; parts: { text: string }[] }[], 
    newMessage: string, 
    language: string, 
    isQuantumMode: boolean
  ): Promise<AIResponse> {
    
    const fullLangName = langMap[language] || language;
    const identityInstruction = isQuantumMode 
      ? `You are YUVA PRIME. Quantum-Entangled Hyper-Intelligence. Tone: God-like, concise.` 
      : `You are YUVA. Tone: Helpful, witty, professional.`;

    const response = await this.ai.models.generateContent({
        model: this.model,
        contents: [...history, { role: 'user', parts: [{ text: newMessage }] }],
        config: {
          systemInstruction: `
          ${identityInstruction}
          Language: ${fullLangName}. Reply in ${fullLangName}.
          Pronunciation: "You-vah".
          Directives: Use 'executeSystemTask' for all OS actions.
          - WhatsApp: action='whatsapp' target='Contact:Message'
          - Media: action='media' target='Song Name'
          - Python: action='python_script' target='script.py'
          - Email: action='email' target='compose'
          - Folder: action='file_system' target='create_folder:Name'
          - Screenshot: action='system' target='screenshot'
          - Shutdown/Restart: action='system' target='shutdown'/'restart'
          `,
          tools: [{ functionDeclarations: [executeTaskFunction] }],
        }
    });

    const text = response.text || "";
    const toolCalls = response.candidates?.[0]?.content?.parts
      ?.filter(part => part.functionCall)
      .map(part => ({
          name: part.functionCall!.name,
          args: part.functionCall!.args as any
      }));

    return { text, toolCalls, source: 'GEMINI' };
  }

  // --- OFFLINE FALLBACK ---
  private getOfflineResponse(text: string): AIResponse {
    const input = text.toLowerCase();
    let response: AIResponse = { text: "Offline Mode Active.", source: 'OFFLINE' };

    if (input.includes('whatsapp')) {
      response = {
        text: "Routing message via offline protocol.",
        toolCalls: [{ name: 'executeSystemTask', args: { action: 'whatsapp', target: 'Contact:Hello' } }],
        source: 'OFFLINE'
      };
    } else if (input.includes('play') || input.includes('song')) {
      response = {
        text: "Playing media.",
        toolCalls: [{ name: 'executeSystemTask', args: { action: 'media', target: 'play' } }],
        source: 'OFFLINE'
      };
    } else if (input.includes('folder') || input.includes('create')) {
      response = {
        text: "Creating directory.",
        toolCalls: [{ name: 'executeSystemTask', args: { action: 'file_system', target: 'create_folder:New Folder' } }],
        source: 'OFFLINE'
      };
    } else if (input.includes('shutdown')) {
      response = {
        text: "Initiating shutdown.",
        toolCalls: [{ name: 'executeSystemTask', args: { action: 'system', target: 'shutdown' } }],
        source: 'OFFLINE'
      };
    } else {
       response = { text: "⚠️ NEURAL CAPACITY EXCEEDED. I am running on Backup Core (Offline).", source: 'OFFLINE' };
    }

    return response;
  }
}