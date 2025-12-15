import React, { useEffect, useState } from 'react';
import { AreaChart, Area, ResponsiveContainer, YAxis } from 'recharts';
import { SystemMetric } from '../types';

interface MonitorProps {
    isQuantum: boolean;
    metrics?: { cpu: number; ram: number; battery: number };
}

const SystemMonitor: React.FC<MonitorProps> = ({ isQuantum, metrics }) => {
    const [cpuData, setCpuData] = useState<SystemMetric[]>([]);
    const [activeTab, setActiveTab] = useState<'sys' | 'env'>('sys');

    // Simulated Environmental Data
    const [envData, setEnvData] = useState({ temp: 24, radiation: 0.12, humidity: 45 });

    const colorPrimary = isQuantum ? '#f59e0b' : '#3b82f6'; // Gold or Blue

    // Initialize data
    useEffect(() => {
        const initialData = Array.from({ length: 20 }, (_, i) => ({
            time: i.toString(),
            value: 0
        }));
        setCpuData(initialData);
    }, []);

    // Update data when metrics change
    useEffect(() => {
        if (metrics) {
            setCpuData(prev => {
                // Keep last 20 points
                const newData = [...prev.slice(1), { time: Date.now().toString(), value: metrics.cpu }];
                return newData;
            });
        }
    }, [metrics]);

    // Environmental simulation loop
    useEffect(() => {
        const interval = setInterval(() => {
            setEnvData(prev => ({
                temp: prev.temp + (Math.random() * 0.4 - 0.2),
                radiation: Math.max(0, prev.radiation + (Math.random() * 0.02 - 0.01)),
                humidity: Math.max(30, Math.min(60, prev.humidity + (Math.random() * 2 - 1)))
            }));
        }, 1000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="h-full w-full flex flex-col gap-3 min-h-0 relative">
            {/* Tabs */}
            <div className="flex gap-2 mb-1">
                <button
                    onClick={() => setActiveTab('sys')}
                    className={`flex-1 py-1 text-[10px] font-hud tracking-widest border transition-all ${activeTab === 'sys' ? `bg-${isQuantum ? 'amber' : 'blue'}-500/20 border-${isQuantum ? 'amber' : 'blue'}-500 text-white` : 'border-transparent text-white/40'}`}
                >
                    SYSTEM
                </button>
                <button
                    onClick={() => setActiveTab('env')}
                    className={`flex-1 py-1 text-[10px] font-hud tracking-widest border transition-all ${activeTab === 'env' ? `bg-${isQuantum ? 'amber' : 'blue'}-500/20 border-${isQuantum ? 'amber' : 'blue'}-500 text-white` : 'border-transparent text-white/40'}`}
                >
                    PLANETARY
                </button>
            </div>

            {activeTab === 'sys' ? (
                <>
                    {/* CPU CHART */}
                    <div className={`flex-1 p-2 border bg-black/40 backdrop-blur rounded-lg flex flex-col overflow-hidden min-h-0 relative ${isQuantum ? 'border-amber-500/30' : 'border-blue-500/30'}`}>
                        <div className="flex justify-between items-center mb-1">
                            <h3 className={`font-hud text-[10px] tracking-widest uppercase ${isQuantum ? 'text-amber-400' : 'text-blue-400'}`}>Neural Load</h3>
                            <div className="flex gap-4">
                                <span className="text-white/70 font-mono text-xs">CPU: {metrics?.cpu.toFixed(0) || 0}%</span>
                                <span className="text-white/70 font-mono text-xs">RAM: {metrics?.ram.toFixed(0) || 0}%</span>
                            </div>
                        </div>
                        <div className="flex-1 min-h-0 relative">
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={cpuData}>
                                    <YAxis domain={[0, 100]} hide />
                                    <defs>
                                        <linearGradient id="colorCpu" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor={colorPrimary} stopOpacity={0.4} />
                                            <stop offset="95%" stopColor={colorPrimary} stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <Area
                                        type="monotone"
                                        dataKey="value"
                                        stroke={colorPrimary}
                                        strokeWidth={2}
                                        fill="url(#colorCpu)"
                                        isAnimationActive={false}
                                    />
                                </AreaChart>
                            </ResponsiveContainer>
                        </div>
                        <div className="mt-1 flex justify-between px-1">
                            <div className="w-full bg-gray-800 h-1 rounded overflow-hidden">
                                <div className={`h-full ${isQuantum ? 'bg-amber-500' : 'bg-green-500'}`} style={{ width: `${metrics?.battery || 100}%` }}></div>
                            </div>
                        </div>
                    </div>
                </>
            ) : (
                <div className={`flex-1 p-3 border bg-black/40 backdrop-blur rounded-lg flex flex-col gap-4 relative overflow-hidden ${isQuantum ? 'border-amber-500/30' : 'border-emerald-500/30'}`}>
                    {/* Environment Data */}
                    <div className="grid grid-cols-2 gap-2 h-full">
                        <div className="bg-white/5 p-2 rounded flex flex-col justify-center items-center">
                            <span className="text-[10px] text-white/50 font-hud">ATMOS TEMP</span>
                            <span className="text-2xl font-mono text-white">{envData.temp.toFixed(1)}°C</span>
                        </div>
                        <div className="bg-white/5 p-2 rounded flex flex-col justify-center items-center">
                            <span className="text-[10px] text-white/50 font-hud">RADIATION</span>
                            <span className={`${isQuantum ? 'text-amber-400' : 'text-red-400'} text-2xl font-mono animate-pulse`}>{envData.radiation.toFixed(3)} Sv</span>
                        </div>
                        <div className="col-span-2 bg-white/5 p-2 rounded flex flex-col justify-center items-center relative overflow-hidden">
                            <span className="text-[10px] text-white/50 font-hud mb-1">GLOBAL NETWORK THREAT</span>
                            <div className="w-full h-2 bg-gray-800 rounded-full overflow-hidden">
                                <div className="h-full bg-red-600 animate-pulse" style={{ width: '12%' }}></div>
                            </div>
                            <span className="text-xs text-red-400 font-mono mt-1">LOW // STABLE</span>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default SystemMonitor;