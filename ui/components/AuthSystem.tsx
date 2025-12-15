import React, { useState } from 'react';

// --- STYLES & ASSETS ---
// Reusing styling from App.tsx via Tailwind classes
// Assuming common sounds are available or we pass a playSound prop

interface AuthProps {
    onAuthSuccess: (user: any) => void;
    playSound: (type: string) => void;
}

const API_URL = "http://localhost:8000";

export const AuthSystem: React.FC<AuthProps> = ({ onAuthSuccess, playSound }) => {
    const [view, setView] = useState<'LOGIN' | 'REGISTER' | 'SUBSCRIPTION'>('LOGIN');
    const [form, setForm] = useState({ username: '', password: '', email: '' });
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const [userPlan, setUserPlan] = useState<'FREE' | 'PRO' | 'ULTRA'>('FREE');

    const handleInput = (e: React.ChangeEvent<HTMLInputElement>) => {
        setForm({ ...form, [e.target.name]: e.target.value });
    };

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true); setError(null);
        try {
            const formData = new URLSearchParams();
            formData.append('username', form.username);
            formData.append('password', form.password);

            const res = await fetch(`${API_URL}/token`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: formData
            });

            if (!res.ok) throw new Error("ACCESS DENIED: Invalid Credentials");

            const data = await res.json();
            localStorage.setItem('jarvis_token', data.access_token);
            playSound('auth_success');

            // Get User Details
            const userRes = await fetch(`${API_URL}/api/me`, {
                headers: { 'Authorization': `Bearer ${data.access_token}` }
            });
            const userData = await userRes.json();

            if (userData.subscription === 'FREE') {
                setView('SUBSCRIPTION'); // Upsell
            } else {
                onAuthSuccess(userData);
            }
        } catch (err: any) {
            playSound('auth_fail');
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleRegister = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true); setError(null);
        try {
            const res = await fetch(`${API_URL}/api/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(form)
            });

            if (!res.ok) {
                const d = await res.json();
                throw new Error(d.detail || "REGISTRATION FAILED");
            }

            playSound('success');
            // Auto Login
            await handleLogin(e);
        } catch (err: any) {
            playSound('auth_fail');
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleSubscribe = async (plan: string) => {
        setLoading(true);
        try {
            const token = localStorage.getItem('jarvis_token');
            const res = await fetch(`${API_URL}/api/subscription`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ plan })
            });
            if (!res.ok) throw new Error("TRANSACTION FAILED");
            playSound('coin');
            // Fetch updated user to confirm
            const userRes = await fetch(`${API_URL}/api/me`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const userData = await userRes.json();
            onAuthSuccess(userData);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-[2000] flex items-center justify-center bg-black font-hud text-cyan-400">
            <div className="absolute inset-0 bg-[url('https://media.giphy.com/media/26tn33aiTi1jkl6H6/giphy.gif')] opacity-10 bg-cover"></div>
            <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-black"></div>

            <div className={`relative w-[500px] min-h-[600px] border border-cyan-500/30 rounded-3xl bg-black/80 backdrop-blur-xl flex flex-col p-8 shadow-[0_0_50px_rgba(6,182,212,0.15)] transition-all duration-500`}>
                <div className="text-center mb-8 relative">
                    <h1 className="text-4xl font-bold tracking-[0.2em] text-white flicker">YUVA OS</h1>
                    <div className="text-xs tracking-[0.5em] text-cyan-500 mt-2 opacity-80">SECURE ACCESS GATEWAY</div>
                    <div className="absolute bottom-[-10px] left-1/2 -translate-x-1/2 w-24 h-1 bg-cyan-500 shadow-[0_0_10px_#22d3ee]"></div>
                </div>

                {error && (
                    <div className="bg-red-500/20 border border-red-500/50 p-3 mb-6 rounded text-red-200 text-xs font-mono text-center animate-pulse">
                        ⚠ {error}
                    </div>
                )}

                {view === 'LOGIN' && (
                    <form onSubmit={handleLogin} className="flex flex-col gap-6 animate-fade-in-up">
                        <div className="space-y-4">
                            <div className="group relative">
                                <label className="text-[10px] tracking-widest text-cyan-600 block mb-1">IDENTITY_ID</label>
                                <input name="username" value={form.username} onChange={handleInput} className="w-full bg-black/50 border border-cyan-500/20 rounded p-3 text-cyan-100 focus:border-cyan-400 focus:shadow-[0_0_15px_rgba(34,211,238,0.2)] outline-none transition-all font-mono" placeholder="USR-001" />
                            </div>
                            <div className="group relative">
                                <label className="text-[10px] tracking-widest text-cyan-600 block mb-1">ACCESS_KEY</label>
                                <input type="password" name="password" value={form.password} onChange={handleInput} className="w-full bg-black/50 border border-cyan-500/20 rounded p-3 text-cyan-100 focus:border-cyan-400 focus:shadow-[0_0_15px_rgba(34,211,238,0.2)] outline-none transition-all font-mono" placeholder="••••••••" />
                            </div>
                        </div>

                        <button disabled={loading} className="mt-4 bg-cyan-500/10 border border-cyan-500/50 py-3 rounded hover:bg-cyan-500/20 hover:shadow-[0_0_20px_rgba(34,211,238,0.3)] transition-all tracking-[0.2em] text-sm font-bold text-cyan-300 disabled:opacity-50">
                            {loading ? 'AUTHENTICATING...' : 'INITIATE SEQUENCE'}
                        </button>

                        <div className="text-center mt-4">
                            <button type="button" onClick={() => { setView('REGISTER'); setError(null); playSound('click'); }} className="text-[10px] text-cyan-600 hover:text-cyan-400 tracking-widest border-b border-transparent hover:border-cyan-400 transition-colors">NO ID FOUND? CREATE IDENTITY</button>
                        </div>
                    </form>
                )}

                {view === 'REGISTER' && (
                    <form onSubmit={handleRegister} className="flex flex-col gap-5 animate-fade-in-up">
                        <div className="space-y-3">
                            <div className="group">
                                <label className="text-[10px] tracking-widest text-cyan-600 block mb-1">NEW_IDENTITY</label>
                                <input name="username" value={form.username} onChange={handleInput} className="w-full bg-black/50 border border-cyan-500/20 rounded p-3 text-cyan-100 focus:border-cyan-400 font-mono" required />
                            </div>
                            <div className="group">
                                <label className="text-[10px] tracking-widest text-cyan-600 block mb-1">COMMS_LINK (EMAIL)</label>
                                <input name="email" value={form.email} onChange={handleInput} className="w-full bg-black/50 border border-cyan-500/20 rounded p-3 text-cyan-100 focus:border-cyan-400 font-mono" />
                            </div>
                            <div className="group">
                                <label className="text-[10px] tracking-widest text-cyan-600 block mb-1">SECURE_PHRASE</label>
                                <input type="password" name="password" value={form.password} onChange={handleInput} className="w-full bg-black/50 border border-cyan-500/20 rounded p-3 text-cyan-100 focus:border-cyan-400 font-mono" required />
                            </div>
                        </div>

                        <button disabled={loading} className="mt-2 bg-cyan-500/10 border border-cyan-500/50 py-3 rounded hover:bg-cyan-500/20 hover:shadow-[0_0_20px_rgba(34,211,238,0.3)] transition-all tracking-[0.2em] text-sm font-bold text-cyan-300 disabled:opacity-50">
                            {loading ? 'PROCESSING...' : 'ESTABLISH IDENTITY'}
                        </button>

                        <div className="text-center mt-2">
                            <button type="button" onClick={() => { setView('LOGIN'); setError(null); playSound('click'); }} className="text-[10px] text-cyan-600 hover:text-cyan-400 tracking-widest">RETURN TO LOGIN</button>
                        </div>
                    </form>
                )}

                {view === 'SUBSCRIPTION' && (
                    <div className="flex flex-col gap-4 animate-fade-in-up h-full overflow-y-auto pr-1 custom-scrollbar">
                        <div className="text-center text-xs text-cyan-300 mb-2">SELECT NEURAL LINK CAPACITY</div>

                        {/* Plans */}
                        {[
                            { id: 'FREE', name: 'NOVICE', price: '₹0', feats: ['Basic Commands', 'Standard Response Time', 'Local Processing'] },
                            { id: 'PRO', name: 'OPERATOR', price: '₹499', feats: ['Advanced AI Models', 'Priority Processing', 'Cloud Sync', 'Voice Customization'], highlight: true },
                            { id: 'ULTRA', name: 'ARCHITECT', price: '₹999', feats: ['Unrestricted Access', 'Quantum Compute Access', 'Developer API', 'Real-time Learning', '24/7 Uplink'] }
                        ].map(p => (
                            <div key={p.id} onClick={() => handleSubscribe(p.id)} className={`relative p-4 border ${p.highlight ? 'border-cyan-400 bg-cyan-500/10 shadow-[0_0_20px_rgba(34,211,238,0.1)]' : 'border-white/10 hover:border-white/30'} rounded-xl cursor-pointer transition-all hover:scale-[1.02] flex flex-col gap-2 group`}>
                                <div className="flex justify-between items-center">
                                    <span className={`font-bold tracking-widest ${p.highlight ? 'text-cyan-300' : 'text-gray-400'}`}>{p.name}</span>
                                    <span className="font-mono text-xl text-white">{p.price}</span>
                                </div>
                                <div className="h-[1px] bg-white/10 w-full my-1"></div>
                                <div className="space-y-1">
                                    {p.feats.map((f, i) => <div key={i} className="text-[10px] text-gray-400 flex items-center gap-2"><span className="text-cyan-500">cs</span> {f}</div>)}
                                </div>
                                {p.highlight && <div className="absolute top-0 right-0 bg-cyan-500 text-black text-[9px] font-bold px-2 py-1 rounded-bl-lg">RECOMMENDED</div>}
                            </div>
                        ))}

                        <button onClick={() => onAuthSuccess({ username: 'User', subscription: 'FREE' })} className="mt-2 text-[10px] text-gray-500 hover:text-white transition-colors">Skip for now (Limited Mode)</button>
                    </div>
                )}
            </div>
        </div>
    );
};
