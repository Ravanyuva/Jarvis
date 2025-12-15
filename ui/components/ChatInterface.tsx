import React, { useEffect, useRef, useState } from 'react';
import { Message } from '../types';

interface ChatInterfaceProps {
    messages: Message[];
}

// Sub-component for Typing Effect
const TypewriterText = ({ text, onComplete }: { text: string, onComplete?: () => void }) => {
    const [displayedText, setDisplayedText] = useState("");

    useEffect(() => {
        let i = 0;
        const interval = setInterval(() => {
            setDisplayedText(text.slice(0, i + 1));
            i++;
            if (i >= text.length) {
                clearInterval(interval);
                if (onComplete) onComplete();
            }
        }, 15); // Typing speed
        return () => clearInterval(interval);
    }, [text]);

    return <span>{displayedText}<span className="animate-pulse">_</span></span>;
};

const ChatInterface: React.FC<ChatInterfaceProps> = ({ messages }) => {
    const endRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        endRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    return (
        <div className="h-full flex flex-col p-4 overflow-y-auto space-y-6 pr-2 font-code scrollbar-hide">
            {messages.map((msg, idx) => {
                const isUser = msg.role === 'user';
                // Only animate the very last message if it's from model
                const isLast = idx === messages.length - 1;
                const animate = !isUser && isLast;

                return (
                    <div
                        key={msg.id}
                        className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} group`}
                    >
                        {/* Label */}
                        <div className={`flex items-center gap-2 mb-1 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
                            <div className={`w-1 h-1 rounded-full ${isUser ? 'bg-emerald-500' : 'bg-cyan-500'}`}></div>
                            <span className={`text-[9px] font-hud tracking-widest uppercase opacity-70 ${isUser ? 'text-emerald-400' : 'text-cyan-400'}`}>
                                {isUser ? 'OPERATOR' : 'YUVA_CORE'}
                            </span>
                            <span className="text-[8px] opacity-30">{msg.timestamp.toLocaleTimeString()}</span>
                        </div>

                        {/* Bubble */}
                        <div className={`max-w-[90%] md:max-w-[80%] text-sm md:text-base relative backdrop-blur-md border ${isUser
                                ? 'border-emerald-500/30 bg-emerald-950/20 text-emerald-100 rounded-tl-xl rounded-bl-xl rounded-br-none rounded-tr-xl'
                                : 'border-cyan-500/30 bg-cyan-950/20 text-cyan-100 rounded-tr-xl rounded-br-xl rounded-bl-none rounded-tl-xl'
                            } p-4 shadow-[0_0_20px_rgba(0,0,0,0.2)] transition-all duration-300 hover:shadow-[0_0_30px_rgba(6,182,212,0.1)]`}>

                            {/* Corner Accents */}
                            <div className={`absolute top-0 w-3 h-3 border-t border-current opacity-50 ${isUser ? 'right-0 border-r' : 'left-0 border-l'}`}></div>
                            <div className={`absolute bottom-0 w-3 h-3 border-b border-current opacity-50 ${isUser ? 'left-0 border-l' : 'right-0 border-r'}`}></div>

                            {msg.isCommand ? (
                                <div className="flex items-center gap-2 text-amber-400 font-bold tracking-wide">
                                    <span>⚡</span>
                                    <span>{msg.text}</span>
                                </div>
                            ) : (
                                <div className="leading-relaxed whitespace-pre-wrap font-mono">
                                    {animate ? <TypewriterText text={msg.text} /> : msg.text}
                                </div>
                            )}
                        </div>
                    </div>
                );
            })}
            <div ref={endRef} />
        </div>
    );
};

export default ChatInterface;