import React from 'react';
import { AppStatus } from '../types';

interface ArcReactorProps {
  status: AppStatus;
  onClick: () => void;
}

const ArcReactor: React.FC<ArcReactorProps> = ({ status, onClick }) => {
  const isListening = status === AppStatus.LISTENING;
  const isSpeaking = status === AppStatus.SPEAKING;
  const isProcessing = status === AppStatus.PROCESSING;

  // Dynamic colors based on state
  let coreColor = "#06b6d4"; // Default Cyan
  if (isListening) coreColor = "#ec4899"; // Pink
  else if (isProcessing) coreColor = "#f59e0b"; // Amber
  else if (isSpeaking) coreColor = "#3b82f6"; // Blue

  return (
    <div 
        className="relative w-96 h-96 flex items-center justify-center cursor-pointer group"
        onClick={onClick}
    >
        {/* SVG CONTAINER */}
        <svg viewBox="0 0 100 100" className="w-full h-full drop-shadow-[0_0_15px_rgba(6,182,212,0.3)]">
            
            {/* DEF: Glow Filters */}
            <defs>
                <filter id="glow">
                    <feGaussianBlur stdDeviation="2.5" result="coloredBlur"/>
                    <feMerge>
                        <feMergeNode in="coloredBlur"/>
                        <feMergeNode in="SourceGraphic"/>
                    </feMerge>
                </filter>
            </defs>

            {/* OUTER RING (Static Tech Marks) */}
            <circle cx="50" cy="50" r="48" fill="none" stroke={coreColor} strokeWidth="0.2" opacity="0.3" />
            <path d="M50 2 A48 48 0 0 1 98 50" fill="none" stroke={coreColor} strokeWidth="0.5" strokeDasharray="4 2" opacity="0.4" />
            <path d="M50 98 A48 48 0 0 1 2 50" fill="none" stroke={coreColor} strokeWidth="0.5" strokeDasharray="4 2" opacity="0.4" />

            {/* RING 1: Slow Rotation */}
            <g className="animate-[spin_20s_linear_infinite] origin-center">
                 <circle cx="50" cy="50" r="40" fill="none" stroke={coreColor} strokeWidth="0.3" strokeDasharray="20 10" opacity="0.5" />
                 <rect x="49" y="8" width="2" height="4" fill={coreColor} opacity="0.8" />
                 <rect x="49" y="88" width="2" height="4" fill={coreColor} opacity="0.8" />
            </g>

            {/* RING 2: Medium Reverse Rotation */}
            <g className="animate-[spin_10s_linear_infinite_reverse] origin-center">
                <circle cx="50" cy="50" r="32" fill="none" stroke={coreColor} strokeWidth="0.8" strokeDasharray="50 40" opacity="0.6" />
                <path d="M50 18 L52 22 L48 22 Z" fill={coreColor} />
            </g>

            {/* RING 3: Fast Spinner (Active State) */}
            <g className={`origin-center transition-all duration-1000 ${isListening || isProcessing ? 'animate-[spin_2s_linear_infinite]' : 'animate-[spin_8s_linear_infinite]'}`}>
                <circle cx="50" cy="50" r="24" fill="none" stroke={coreColor} strokeWidth="1" strokeDasharray="10 30" opacity="0.8" filter="url(#glow)" />
            </g>

            {/* INNER CORE (Pulsing) */}
            <g className="animate-pulse">
                <circle cx="50" cy="50" r="14" fill={coreColor} opacity="0.1" />
                <circle cx="50" cy="50" r="8" fill={coreColor} opacity="0.4" filter="url(#glow)" />
                <circle cx="50" cy="50" r="4" fill="#ffffff" opacity="0.8" filter="url(#glow)" />
            </g>
            
            {/* Audio Wave Visualization (Simulated) */}
            {isSpeaking && (
                <g className="origin-center">
                    <circle cx="50" cy="50" r="18" fill="none" stroke={coreColor} strokeWidth="0.5" className="animate-ping opacity-50" />
                    <circle cx="50" cy="50" r="28" fill="none" stroke={coreColor} strokeWidth="0.2" className="animate-ping opacity-30 animation-delay-500" />
                </g>
            )}
        </svg>

        {/* Text Label Overlay */}
        <div className="absolute bottom-10 left-1/2 -translate-x-1/2 text-center pointer-events-none">
            <div className={`text-[10px] font-hud tracking-[0.3em] uppercase transition-colors duration-300 ${isListening ? 'text-pink-400' : 'text-cyan-400'}`}>
                {status}
            </div>
            <div className="text-[8px] font-code opacity-50 tracking-widest mt-1">
                SYSTEM_READY
            </div>
        </div>
    </div>
  );
};

export default ArcReactor;