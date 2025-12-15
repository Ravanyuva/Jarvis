import React, { useState, useEffect, useRef, useCallback } from 'react';
// import { GeminiService } from './services/geminiService'; // REMOVED
import ArcReactor from './components/ArcReactor';
import SystemMonitor from './components/SystemMonitor';
import ChatInterface from './components/ChatInterface';
import { AuthSystem } from './components/AuthSystem';
import { AppStatus, Message } from './types';

// const geminiService = new GeminiService(); // REMOVED

// --- CONFIGURATION ---
const LANGUAGES = [
    { code: 'en-US', label: 'ENG (US)' },
    { code: 'en-GB', label: 'ENG (UK)' },
    { code: 'en-IN', label: 'ENG (IN)' },
    { code: 'hi-IN', label: 'HINDI' },
    { code: 'kn-IN', label: 'KANNADA' },
    { code: 'ta-IN', label: 'TAMIL' },
    { code: 'te-IN', label: 'TELUGU' },
    { code: 'ml-IN', label: 'MALAYALAM' },
    { code: 'ja-JP', label: 'JAPANESE' },
    { code: 'zh-CN', label: 'CHINESE' }
];

// --- UTILS: SOUND & BOOT ---
const playSound = (type: string) => {
    try {
        const AudioContext = window.AudioContext || (window as any).webkitAudioContext;
        if (!AudioContext) return;
        const ctx = new AudioContext();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.connect(gain);
        gain.connect(ctx.destination);
        const now = ctx.currentTime;

        if (type === 'click') {
            osc.type = 'sine'; osc.frequency.setValueAtTime(800, now); gain.gain.setTargetAtTime(0, now, 0.1);
        } else if (type === 'boot') {
            osc.type = 'triangle'; osc.frequency.setValueAtTime(100, now);
            osc.frequency.linearRampToValueAtTime(600, now + 1);
            gain.gain.setValueAtTime(0, now); gain.gain.linearRampToValueAtTime(0.1, now + 0.5); gain.gain.linearRampToValueAtTime(0, now + 3);
        } else if (type === 'alert') {
            osc.type = 'square'; osc.frequency.setValueAtTime(600, now);
            osc.frequency.linearRampToValueAtTime(800, now + 0.2);
            gain.gain.setValueAtTime(0, now); gain.gain.linearRampToValueAtTime(0.1, now + 0.1); gain.gain.linearRampToValueAtTime(0, now + 0.5);
        } else if (type === 'shutter') {
            osc.type = 'sawtooth'; osc.frequency.setValueAtTime(800, now);
            osc.frequency.exponentialRampToValueAtTime(100, now + 0.1);
            gain.gain.setValueAtTime(0.3, now); gain.gain.exponentialRampToValueAtTime(0.001, now + 0.1);
        } else if (type === 'shutdown') {
            osc.type = 'sawtooth'; osc.frequency.setValueAtTime(400, now);
            osc.frequency.exponentialRampToValueAtTime(10, now + 2);
            gain.gain.setValueAtTime(0.2, now); gain.gain.linearRampToValueAtTime(0, now + 2);
        } else if (type === 'auth_success') {
            osc.type = 'triangle'; osc.frequency.setValueAtTime(400, now); osc.frequency.linearRampToValueAtTime(800, now + 0.2);
            gain.gain.setValueAtTime(0.1, now); gain.gain.linearRampToValueAtTime(0, now + 0.4);
        } else if (type === 'auth_fail') {
            osc.type = 'sawtooth'; osc.frequency.setValueAtTime(150, now); osc.frequency.linearRampToValueAtTime(100, now + 0.3);
            gain.gain.setValueAtTime(0.1, now); gain.gain.linearRampToValueAtTime(0, now + 0.3);
        } else if (type === 'sent') {
            osc.type = 'sine'; osc.frequency.setValueAtTime(400, now); osc.frequency.exponentialRampToValueAtTime(1200, now + 0.3);
            gain.gain.setValueAtTime(0.1, now); gain.gain.linearRampToValueAtTime(0, now + 0.4);
        } else if (type === 'process') {
            osc.type = 'square'; osc.frequency.setValueAtTime(200, now);
            osc.frequency.linearRampToValueAtTime(800, now + 0.1);
            gain.gain.setValueAtTime(0.1, now); gain.gain.exponentialRampToValueAtTime(0.001, now + 0.2);
        }
        osc.start(now); osc.stop(now + 3);
    } catch (e) { }
};

// SecurityGate removed in favor of AuthSystem

// --- EMAIL CLIENT SIMULATION ---
const EmailClient = ({ onClose }: { onClose: () => void }) => {
    const [sending, setSending] = useState(false);
    const [sent, setSent] = useState(false);
    const handleSend = () => {
        setSending(true);
        setTimeout(() => { setSending(false); setSent(true); playSound('sent'); setTimeout(onClose, 1500); }, 2000);
    };
    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm animate-fade-in-up">
            <div className="w-[600px] h-[400px] bg-black/80 border border-cyan-500/30 rounded-lg shadow-[0_0_50px_rgba(6,182,212,0.2)] flex flex-col font-mono relative overflow-hidden">
                <div className="h-10 bg-cyan-950/30 border-b border-cyan-500/20 flex items-center justify-between px-4">
                    <span className="text-cyan-400 font-bold tracking-widest text-xs">YUVAMAIL // COMPOSER</span>
                    <button onClick={onClose} className="text-red-400 hover:text-red-300">✖</button>
                </div>
                {sent ? (
                    <div className="flex-1 flex flex-col items-center justify-center text-emerald-400 gap-4">
                        <div className="w-16 h-16 border-2 border-emerald-400 rounded-full flex items-center justify-center text-2xl animate-bounce">✓</div>
                        <span className="tracking-widest">TRANSMISSION SECURE</span>
                    </div>
                ) : (
                    <div className="flex-1 p-6 flex flex-col gap-4 text-cyan-100/80 text-sm">
                        <input type="text" className="bg-transparent border-b border-cyan-500/30 py-1 focus:outline-none focus:border-cyan-400" placeholder="Recipient" />
                        <input type="text" className="bg-transparent border-b border-cyan-500/30 py-1 focus:outline-none focus:border-cyan-400" placeholder="Subject" />
                        <textarea className="bg-transparent border border-cyan-500/30 rounded p-2 h-full resize-none focus:outline-none focus:border-cyan-400" placeholder="Message..."></textarea>
                        <div className="flex justify-end"><button onClick={handleSend} disabled={sending} className="bg-cyan-600/20 border border-cyan-500/50 px-6 py-2 rounded text-cyan-300 hover:bg-cyan-500/30">{sending ? 'SENDING...' : 'SEND'}</button></div>
                    </div>
                )}
            </div>
        </div>
    );
};

// --- WHATSAPP CLIENT SIMULATION ---
const WhatsAppClient = ({ target, onClose }: { target: string, onClose: () => void }) => {
    const [status, setStatus] = useState("LOCATING CONTACT...");
    useEffect(() => {
        setTimeout(() => setStatus("CONTACT FOUND: " + target.split(':')[0]), 1000);
        setTimeout(() => setStatus("TYPING MESSAGE..."), 2000);
        setTimeout(() => setStatus("SENDING ENCRYPTED PAYLOAD..."), 3500);
        setTimeout(() => { playSound('sent'); onClose(); }, 5000);
    }, [target, onClose]);

    return (
        <div className="fixed bottom-10 right-10 w-80 bg-[#0b141a] border border-green-500/30 rounded-lg shadow-2xl overflow-hidden font-sans animate-fade-in-up z-50">
            <div className="bg-[#202c33] p-3 flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-gray-500"></div>
                <div className="text-gray-200 text-sm font-bold">{target.split(':')[0]}</div>
            </div>
            <div className="h-48 bg-[#0b141a] p-4 flex flex-col justify-end gap-2 bg-[url('https://user-images.githubusercontent.com/15075759/28719144-86dc0f70-73b1-11e7-911d-60d70fcded21.png')] bg-opacity-10">
                <div className="self-end bg-[#005c4b] text-[#e9edef] p-2 rounded-lg text-xs rounded-tr-none animate-pulse">
                    {target.split(':')[1]}
                </div>
            </div>
            <div className="bg-[#202c33] p-2 text-xs text-green-500 text-center font-mono">
                {status}
            </div>
        </div>
    );
};

// --- MEDIA PLAYER SIMULATION ---
const MediaPlayer = ({ song, onClose }: { song: string, onClose: () => void }) => {
    return (
        <div className="fixed bottom-10 left-10 w-80 bg-black/80 border border-purple-500/30 rounded-2xl p-4 backdrop-blur-xl z-50 animate-fade-in-up flex gap-4 items-center">
            <div className="w-16 h-16 bg-purple-900/50 rounded-lg flex items-center justify-center animate-pulse">
                <svg className="w-8 h-8 text-purple-400" fill="currentColor" viewBox="0 0 24 24"><path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z" /></svg>
            </div>
            <div className="flex-1 overflow-hidden">
                <div className="text-purple-300 font-bold text-sm truncate">{song}</div>
                <div className="text-purple-500/60 text-xs font-mono">Unknown Artist</div>
                <div className="flex items-center gap-1 mt-2 h-3">
                    {[...Array(10)].map((_, i) => (
                        <div key={i} className="w-1 bg-purple-500 animate-wave" style={{ height: Math.random() * 100 + '%', animationDelay: i * 0.1 + 's' }}></div>
                    ))}
                </div>
            </div>
            <button onClick={onClose} className="text-white/30 hover:text-white">✕</button>
        </div>
    );
};

// --- DOWNLOADS WINDOW ---
const DownloadsWindow = ({ onClose }: { onClose: () => void }) => {
    return (
        <div className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[400px] bg-black/90 border border-cyan-500/30 rounded-lg shadow-2xl p-4 font-mono z-50 animate-fade-in-up flex flex-col">
            <div className="flex justify-between items-center border-b border-cyan-500/20 pb-2 mb-4">
                <span className="text-cyan-400 font-bold">~/USER/DOWNLOADS</span>
                <button onClick={onClose} className="text-red-400">✖</button>
            </div>
            <div className="flex-1 overflow-y-auto space-y-2 text-xs text-cyan-200/80">
                {['project_alpha_v2.zip', 'scan_results_42.pdf', 'neural_net_weights.h5', 'screenshot_001.png'].map((f, i) => (
                    <div key={i} className="flex items-center gap-4 hover:bg-cyan-500/10 p-2 rounded cursor-pointer">
                        <span className="opacity-50">[{new Date().toLocaleDateString()}]</span>
                        <span className="flex-1">{f}</span>
                        <span className="text-cyan-500">{(Math.random() * 50).toFixed(1)} MB</span>
                    </div>
                ))}
            </div>
        </div>
    );
};

// --- PYTHON TERMINAL COMPONENT ---
const PythonTerminal = ({ scriptName, onClose }: { scriptName: string, onClose: () => void }) => {
    const [lines, setLines] = useState<string[]>([]);
    useEffect(() => {
        const base = [`> python ${scriptName}`, `[PY_KERNEL] Initializing...`];
        let spec = [`> Executing logic...`, `[STDOUT] Task completed.`];
        if (scriptName.includes('data')) spec = [`> Importing pandas...`, `[INFO] Shape: (1000, 5)`, `[SUCCESS] Exported.`];
        if (scriptName.includes('net')) spec = [`> Scanning ports...`, `[WARN] Open: 8080`, `[SUCCESS] Done.`];
        const all = [...base, ...spec, `[EXIT] Code 0.`];
        let i = 0;
        const int = setInterval(() => { if (i < all.length) { setLines(p => [...p, all[i]]); playSound('process'); i++; } else { clearInterval(int); setTimeout(onClose, 2000); } }, 500);
        return () => clearInterval(int);
    }, [scriptName, onClose]);
    return (
        <div className="fixed bottom-10 right-10 z-50 w-[500px] h-[300px] bg-black/90 border border-green-500/40 rounded-lg shadow-2xl font-mono text-xs p-4 flex flex-col animate-fade-in-up">
            <div className="border-b border-green-500/20 pb-2 mb-2 text-green-500 font-bold">PYTHON TERMINAL // {scriptName}</div>
            <div className="space-y-1 text-green-400/80">{lines.map((l, i) => <div key={i}>{l}</div>)}</div>
        </div>
    );
};

// --- SETTINGS MODAL ---
interface SettingsProps {
    onClose: () => void;
    quantumColor: 'amber' | 'red' | 'purple'; setQuantumColor: (c: 'amber' | 'red' | 'purple') => void;
    quantumPitch: number; setQuantumPitch: (p: number) => void;
    isQuantum: boolean; setIsQuantum: (val: boolean) => void;
    onTestVoice: () => void;
}
const SettingsModal: React.FC<SettingsProps> = ({ onClose, quantumColor, setQuantumColor, quantumPitch, setQuantumPitch, isQuantum, setIsQuantum, onTestVoice }) => {
    return (
        <div className="fixed inset-0 z-[1000] flex items-center justify-center bg-black/80 backdrop-blur-sm">
            <div className={`w-[500px] bg-black/90 border rounded-2xl shadow-2xl overflow-hidden font-sans transition-colors duration-300 ${isQuantum ? (quantumColor === 'red' ? 'border-red-500/30' : quantumColor === 'purple' ? 'border-purple-500/30' : 'border-amber-500/30') : 'border-cyan-500/30'}`}>
                <div className="h-12 border-b flex items-center justify-between px-6 border-white/10 bg-white/5">
                    <span className="font-hud tracking-[0.2em] text-sm text-white/80">SYSTEM CONFIGURATION</span>
                    <button onClick={onClose} className="text-white/50 hover:text-white">✖</button>
                </div>
                <div className="p-8 flex flex-col gap-8">
                    <div className="flex items-center justify-between p-4 bg-white/5 rounded-xl border border-white/10">
                        <div className="flex flex-col"><span className="text-sm font-bold font-hud text-white">QUANTUM PROTOCOL</span><span className="text-[10px] text-white/40 font-mono">Unlock advanced processing & custom themes.</span></div>
                        <button onClick={() => { setIsQuantum(!isQuantum); playSound('click'); }} className={`w-12 h-6 rounded-full relative transition-colors duration-300 ${isQuantum ? (quantumColor === 'red' ? 'bg-red-500' : quantumColor === 'purple' ? 'bg-purple-500' : 'bg-amber-500') : 'bg-gray-700'}`}><div className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform duration-300 ${isQuantum ? 'left-7' : 'left-1'}`}></div></button>
                    </div>
                    <div className={`${!isQuantum && 'opacity-50 grayscale pointer-events-none'}`}>
                        <div className="text-[10px] font-hud text-white/60 tracking-widest mb-4 uppercase">Quantum Theme Matrix</div>
                        <div className="flex gap-4">
                            {[{ id: 'amber', bg: 'bg-amber-500', label: 'SOLAR' }, { id: 'red', bg: 'bg-red-500', label: 'CRIMSON' }, { id: 'purple', bg: 'bg-purple-500', label: 'VOID' }].map((theme) => (
                                <button key={theme.id} onClick={() => { setQuantumColor(theme.id as any); playSound('click'); }} className={`flex-1 h-24 rounded-xl border flex flex-col items-center justify-center gap-2 transition-all ${quantumColor === theme.id ? `border-${theme.id}-500 bg-white/10` : 'border-white/10'}`}><div className={`w-4 h-4 rounded-full ${theme.bg}`}></div><span className="text-[10px] font-code text-white">{theme.label}</span></button>
                            ))}
                        </div>
                    </div>
                    <div className={`${!isQuantum && 'opacity-50 grayscale pointer-events-none'}`}>
                        <div className="text-[10px] font-hud text-white/60 tracking-widest mb-4 uppercase">Vocal Pitch</div>
                        <div className="flex items-center gap-4"><input type="range" min="0.1" max="1.5" step="0.1" value={quantumPitch} onChange={(e) => setQuantumPitch(parseFloat(e.target.value))} className="flex-1 h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer" /></div>
                        <div className="flex justify-between items-center mt-3"><span className="font-mono text-xs text-white/40">{quantumPitch.toFixed(1)} PITCH FACTOR</span><button onClick={onTestVoice} className="px-3 py-1 bg-white/10 border border-white/20 rounded text-[10px] font-hud hover:bg-white/20">TEST VOCAL</button></div>
                    </div>
                </div>
            </div>
        </div>
    );
};

const BootSequence = ({ onComplete }: { onComplete: () => void }) => {
    const [log, setLog] = useState<string[]>([]);
    useEffect(() => {
        playSound('boot');
        const lines = ["INITIALIZING KERNEL...", "DETECTING NEURAL CORES...", "ESTABLISHING SECURE CONNECTION...", "YUVA OS v5.0 ONLINE"];
        let i = 0; const int = setInterval(() => { if (i < lines.length) { setLog(p => [...p, lines[i]]); i++; } else { clearInterval(int); setTimeout(onComplete, 800); } }, 600);
        return () => clearInterval(int);
    }, [onComplete]);
    return <div className="fixed inset-0 bg-black z-[2000] flex flex-col items-center justify-center font-code text-cyan-500"><div className="w-64 h-1 bg-gray-900 rounded mb-4 overflow-hidden"><div className="h-full bg-cyan-400 animate-[width_3s_ease-out_forwards]" style={{ width: '100%' }}></div></div><div className="flex flex-col gap-1 items-start w-64 text-xs">{log.map((l, i) => <div key={i} className="animate-fade-in-up">{`> ${l}`}</div>)}</div></div>;
};

const PowerSequence = ({ type, onComplete }: { type: 'SHUTDOWN' | 'RESTART', onComplete: () => void }) => {
    const [log, setLog] = useState<string[]>([]);
    const [screenOff, setScreenOff] = useState(false);
    useEffect(() => {
        playSound('shutdown');
        const lines = type === 'SHUTDOWN' ? ["TERMINATING...", "STOPPING SERVICES...", "GOODBYE."] : ["REBOOTING...", "CLEARING CACHE...", "RESTARTING..."];
        let i = 0; const int = setInterval(() => { if (i < lines.length) { setLog(p => [...p, lines[i]]); i++; } else { clearInterval(int); setTimeout(() => { setScreenOff(true); setTimeout(onComplete, 1500); }, 500); } }, 500);
        return () => clearInterval(int);
    }, [type, onComplete]);
    if (screenOff && type === 'SHUTDOWN') return <div className="fixed inset-0 bg-black z-[3000] cursor-none"></div>;
    return <div className="fixed inset-0 bg-black z-[3000] flex flex-col items-center justify-center font-code text-red-500"><div className="text-xl tracking-[0.3em] animate-pulse mb-8 font-bold">{type}</div><div className="flex flex-col gap-1 items-start w-80 text-xs">{log.map((l, i) => <div key={i} className="animate-fade-in-up">{`> ${l}`}</div>)}</div></div>;
};

const App: React.FC = () => {
    const [booted, setBooted] = useState(false);
    const [powerState, setPowerState] = useState<'ON' | 'SHUTDOWN' | 'RESTART'>('ON');
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [isQuantum, setIsQuantum] = useState(false);

    const [messages, setMessages] = useState<Message[]>([]);
    const [status, setStatus] = useState<AppStatus>(AppStatus.IDLE);
    const [inputText, setInputText] = useState('');
    const [currentLang, setCurrentLang] = useState('en-US');
    const [aiSource, setAiSource] = useState<'OLLAMA' | 'GEMINI' | 'OFFLINE'>('OFFLINE'); // Default to OFFLINE (Backend)

    const [quantumColor, setQuantumColor] = useState<'amber' | 'red' | 'purple'>('amber');
    const [quantumPitch, setQuantumPitch] = useState(0.6);
    const [showSettings, setShowSettings] = useState(false);
    const [showEmail, setShowEmail] = useState(false);
    const [pythonScript, setPythonScript] = useState<string | null>(null);

    const [whatsAppTarget, setWhatsAppTarget] = useState<string | null>(null);
    const [mediaSong, setMediaSong] = useState<string | null>(null);
    const [showDownloads, setShowDownloads] = useState(false);
    const [sysStats, setSysStats] = useState({ cpu: 0, ram: 0, battery: 100 });

    const recognitionRef = useRef<any>(null);
    const synthRef = useRef<SpeechSynthesis>(window.speechSynthesis);
    const isMicActive = useRef(false);
    const ws = useRef<WebSocket | null>(null);

    const getTheme = () => {
        if (!isQuantum) return { text: 'text-cyan-50', accent: 'text-cyan-400', border: 'border-cyan-500/30', bg: 'bg-cyan-950/10', glow: 'shadow-[0_0_30px_rgba(6,182,212,0.15)]', indicator: 'bg-cyan-500' };
        switch (quantumColor) {
            case 'red': return { text: 'text-red-50', accent: 'text-red-500', border: 'border-red-500/40', bg: 'bg-red-950/20', glow: 'shadow-[0_0_40px_rgba(239,68,68,0.3)]', indicator: 'bg-red-500' };
            case 'purple': return { text: 'text-purple-50', accent: 'text-purple-500', border: 'border-purple-500/40', bg: 'bg-purple-950/20', glow: 'shadow-[0_0_40px_rgba(168,85,247,0.3)]', indicator: 'bg-purple-500' };
            default: return { text: 'text-amber-50', accent: 'text-amber-500', border: 'border-amber-500/40', bg: 'bg-amber-950/20', glow: 'shadow-[0_0_40px_rgba(245,158,11,0.3)]', indicator: 'bg-amber-500' };
        }
    };
    const theme = getTheme();

    const speak = useCallback((text: string) => {
        // Do NOT cancel previous speech, let it queue
        // if (synthRef.current.speaking) synthRef.current.cancel(); 
        
        // Clean text for pronunciation
        let spokenText = text;
        if (currentLang.startsWith('en')) spokenText = text.replace(/YUVA/g, "You-vah");
        
        const utterance = new SpeechSynthesisUtterance(spokenText);
        
        // Ensure voices are loaded
        let voices = synthRef.current.getVoices();
        if (voices.length === 0) {
            // Retry once if voices aren't ready
             setTimeout(() => {
                 voices = synthRef.current.getVoices();
                 const voice = voices.find(v => v.lang === currentLang) || voices[0];
                 if (voice) utterance.voice = voice;
                 synthRef.current.speak(utterance);
             }, 500);
             return;
        }

        const voice = voices.find(v => v.lang === currentLang) || voices[0];
        utterance.voice = voice;
        utterance.pitch = isQuantum ? quantumPitch : 1.0; // Slightly more natural pitch
        utterance.rate = 1.0;
        
        utterance.onstart = () => setStatus(AppStatus.SPEAKING);
        utterance.onend = () => setStatus(AppStatus.IDLE);
        
        synthRef.current.speak(utterance);
    }, [currentLang, isQuantum, quantumPitch]);

    const addMessage = (role: 'user' | 'model', text: string, isCommand = false) => {
        setMessages(prev => [...prev, { id: Date.now().toString(), role, text, timestamp: new Date(), isCommand }]);
    };

    const takeScreenshot = async () => {
        addMessage('model', "INITIATING SCREEN CAPTURE...", true);
        try {
            const stream = await navigator.mediaDevices.getDisplayMedia({ video: { mediaSource: 'screen' } as any });
            const video = document.createElement('video'); video.srcObject = stream;
            await new Promise((r) => { video.onloadedmetadata = () => { video.play(); setTimeout(r, 500); }; });
            const canvas = document.createElement('canvas'); canvas.width = video.videoWidth; canvas.height = video.videoHeight;
            const ctx = canvas.getContext('2d'); ctx?.drawImage(video, 0, 0);
            const link = document.createElement('a'); link.download = `shot-${Date.now()}.png`; link.href = canvas.toDataURL('image/png'); link.click();
            stream.getTracks()[0].stop(); playSound('shutter'); addMessage('model', "SAVED.", true);
        } catch (e) { addMessage('model', "CANCELLED.", true); }
    };

    // --- WEBSOCKET CONNECTION ---
    const connectWs = () => {
        ws.current = new WebSocket('ws://localhost:8000/ws');

        ws.current.onopen = () => {
            console.log('Connected to Jarvis Backend');
            // Auto-start Jarvis Hotword Listener
            ws.current?.send(JSON.stringify({ action: "start" }));
        };

        ws.current.onclose = () => {
            console.log('Disconnected from Jarvis Backend');
            // Try reconnect loop
            setTimeout(connectWs, 3000);
        };

        ws.current.onmessage = (event) => {
            const msg = JSON.parse(event.data);
            if (msg.type === 'status') {
                // Map backend status to UI status
                const s = msg.data;
                if (s === 'listening') setStatus(AppStatus.LISTENING);
                else if (s === 'processing') setStatus(AppStatus.PROCESSING);
                else if (s === 'idle') setStatus(AppStatus.IDLE);
            } else if (msg.type === 'transcript') {
                addMessage('user', msg.data);
            } else if (msg.type === 'speak') {
                addMessage('model', msg.data);
                speak(msg.data);
            } else if (msg.type === 'stats') {
                setSysStats(msg.data);
            }
        };
    };

    useEffect(() => {
        connectWs();
        return () => { if (ws.current) ws.current.close(); };
    }, []);

    const processResponse = async (text: string) => {
        setStatus(AppStatus.PROCESSING);
        // Send command to backend
        if (ws.current && ws.current.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify({ action: "command", text }));
        } else {
            addMessage('model', "OFFLINE MODE: Cannot connect to Core.", true);
            setStatus(AppStatus.IDLE);
        }

        // We don't wait for response here, WS onmessage handles it.
    };

    const toggleListening = () => {
        if (!recognitionRef.current) return;
        playSound('click');
        if (isMicActive.current) {
            try { recognitionRef.current.stop(); } catch (e) { }
            isMicActive.current = false; setStatus(AppStatus.IDLE);
        } else {
            try { recognitionRef.current.start(); isMicActive.current = true; setStatus(AppStatus.LISTENING); }
            catch (e) { isMicActive.current = true; setStatus(AppStatus.LISTENING); }
        }
    };

    useEffect(() => {
        if ('Notification' in window && Notification.permission !== 'granted') Notification.requestPermission();
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
            recognitionRef.current = new SpeechRecognition();
            recognitionRef.current.continuous = false;
            recognitionRef.current.lang = currentLang;
            recognitionRef.current.onresult = (e: any) => {
                const t = e.results[0][0].transcript;
                // Don't add message here, wait for backend transcript event? 
                // Actually backend transcript comes from backend listening.
                // Here we are doing local listening.
                addMessage('user', t);
                processResponse(t);
            };
            recognitionRef.current.onend = () => { if (status === AppStatus.LISTENING) setStatus(AppStatus.IDLE); isMicActive.current = false; };
        }
    }, [currentLang, status]);

    const handleBootComplete = useCallback(() => {
        setBooted(true);
    }, []);

    if (powerState !== 'ON') return <PowerSequence type={powerState} onComplete={() => powerState === 'RESTART' && window.location.reload()} />;
    if (!booted) return <BootSequence onComplete={handleBootComplete} />;
    if (!isAuthenticated) return <AuthSystem onAuthSuccess={(user) => {
        setIsAuthenticated(true);
        addMessage('model', `WELCOME BACK, ${user.username.toUpperCase()}. SUBSCRIPTION: ${user.subscription}. SYSTEM ONLINE.`);
    }} playSound={playSound} />;

    return (
        <div className={`w-full h-screen overflow-hidden relative font-sans transition-colors duration-1000 bg-black ${theme.text}`}>
            <div className="scanlines"></div><div className="vignette"></div>
            <div className={`absolute top-0 w-full h-[2px] opacity-50 bg-gradient-to-r from-transparent to-transparent ${isQuantum ? (quantumColor === 'red' ? 'via-red-500' : quantumColor === 'purple' ? 'via-purple-500' : 'via-amber-500') : 'via-cyan-500'}`}></div>

            {showSettings && <SettingsModal onClose={() => setShowSettings(false)} quantumColor={quantumColor} setQuantumColor={setQuantumColor} quantumPitch={quantumPitch} setQuantumPitch={setQuantumPitch} isQuantum={isQuantum} setIsQuantum={setIsQuantum} onTestVoice={() => speak("Voice systems calibrated.")} />}
            {showEmail && <EmailClient onClose={() => setShowEmail(false)} />}
            {pythonScript && <PythonTerminal scriptName={pythonScript} onClose={() => setPythonScript(null)} />}
            {whatsAppTarget && <WhatsAppClient target={whatsAppTarget} onClose={() => setWhatsAppTarget(null)} />}
            {mediaSong && <MediaPlayer song={mediaSong} onClose={() => setMediaSong(null)} />}
            {showDownloads && <DownloadsWindow onClose={() => setShowDownloads(false)} />}

            <div className="absolute top-0 w-full h-16 flex items-center justify-between px-8 z-30 bg-gradient-to-b from-black/90 to-transparent pointer-events-none">
                <div className="flex items-center gap-3 pointer-events-auto"><div className={`w-3 h-3 rounded-full animate-pulse shadow-[0_0_10px_currentColor] ${theme.indicator}`}></div><span className={`font-hud text-xl tracking-[0.2em] font-bold ${theme.accent} drop-shadow-lg`}>YUVA<span className="opacity-50 font-light">OS</span></span></div>
                <div className="flex gap-4 items-center pointer-events-auto">
                    <div className="hidden md:flex flex-col items-end mr-4"><span className="text-[9px] font-hud opacity-60 tracking-widest">ACTIVE CORE</span><span className={`text-xs font-code font-bold ${aiSource === 'OLLAMA' ? 'text-green-400' : aiSource === 'GEMINI' ? 'text-blue-400' : 'text-red-400'}`}>{aiSource}</span></div>
                    <select value={currentLang} onChange={(e) => setCurrentLang(e.target.value)} className={`bg-black/40 border ${theme.border} text-xs font-code py-1 px-2 rounded uppercase cursor-pointer hover:bg-white/5 transition-colors focus:outline-none`}>{LANGUAGES.map(l => <option key={l.code} value={l.code}>{l.label}</option>)}</select>
                    <button onClick={() => setShowSettings(true)} className={`p-2 rounded hover:bg-white/10 transition-colors ${theme.accent}`} title="Config"><svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg></button>
                </div>
            </div>

            <div className="relative z-10 w-full h-full flex items-center justify-between p-4 md:p-8 pt-20 gap-4 md:gap-8">
                <div className={`w-[350px] h-full flex flex-col border ${theme.border} bg-black/40 backdrop-blur-xl rounded-2xl shadow-2xl overflow-hidden transition-all duration-500`}>
                    <div className={`h-8 border-b ${theme.border} bg-white/5 flex items-center px-4`}><span className="font-hud text-[10px] tracking-widest opacity-60">NEURAL_FEED</span></div>
                    <div className="flex-1 overflow-hidden relative bg-gradient-to-b from-transparent to-black/40"><ChatInterface messages={messages} /></div>
                    <div className="p-4 border-t border-white/5 bg-black/40">
                        <input value={inputText} onChange={(e) => setInputText(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && inputText && (addMessage('user', inputText), processResponse(inputText), setInputText(''))} placeholder="ENTER COMMAND SEQUENCE..." className={`w-full bg-transparent border-b ${theme.border} py-2 text-sm font-code focus:outline-none placeholder-white/20 tracking-wider`} />
                    </div>
                </div>
                <div className="flex-1 h-full flex flex-col items-center justify-center relative">
                    <div className="relative group cursor-pointer">
                        <ArcReactor status={status} onClick={toggleListening} />
                    </div>
                </div>
                <div className={`w-[300px] h-full flex flex-col gap-4 border ${theme.border} bg-black/40 backdrop-blur-xl rounded-2xl p-4 shadow-2xl transition-all duration-500`}>
                    <div className="absolute top-0 right-0 p-2 opacity-50 font-hud text-[9px] tracking-widest">SYS_DIAGNOSTICS</div>
                    <SystemMonitor isQuantum={isQuantum} metrics={sysStats} />
                </div>
            </div>
        </div>
    );
};

export default App;