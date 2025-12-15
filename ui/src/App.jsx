import { useState, useEffect, useRef } from 'react'

function App() {
  const [status, setStatus] = useState('offline') // offline, idle, listening, speaking
  const [transcript, setTranscript] = useState([])
  const [sysStats, setSysStats] = useState({ cpu: 0, ram: 0, battery: 100 })
  const [lastMessage, setLastMessage] = useState("")
  const ws = useRef(null)

  // Connect to WebSocket
  useEffect(() => {
    connectWs()
    return () => {
      if (ws.current) ws.current.close()
    }
  }, [])

  const connectWs = () => {
    ws.current = new WebSocket('ws://localhost:8000/ws')

    ws.current.onopen = () => {
      console.log('Connected')
      setStatus('idle')
      // Auto-start Jarvis
      ws.current.send(JSON.stringify({ action: "start" }))
    }

    ws.current.onclose = () => {
      console.log('Disconnected')
      setStatus('offline')
      // Try reconnect loop
      setTimeout(connectWs, 3000)
    }

    ws.current.onmessage = (event) => {
      const msg = JSON.parse(event.data)
      if (msg.type === 'status') {
        setStatus(msg.data === 'started' ? 'idle' : msg.data === 'stopped' ? 'offline' : msg.data)
      } else if (msg.type === 'transcript') {
        setLastMessage(msg.data)
        setTranscript(prev => [...prev.slice(-4), { text: msg.data, role: 'user', time: new Date().toLocaleTimeString() }])
      } else if (msg.type === 'speak') {
        setTranscript(prev => [...prev.slice(-4), { text: msg.data, role: 'jarvis', time: new Date().toLocaleTimeString() }])
      } else if (msg.type === 'stats') {
        setSysStats(msg.data)
      }
    }
  }

  // TTS Effect
  useEffect(() => {
    if (transcript.length > 0) {
      const last = transcript[transcript.length - 1]
      if (last.role === 'jarvis') {
        const u = new SpeechSynthesisUtterance(last.text)
        window.speechSynthesis.speak(u)
      }
    }
  }, [transcript])

  const sendCommand = (text) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ action: "command", text }))
    }
  }

  return (
    <div className="relative w-full h-full flex flex-col items-center justify-between p-8 text-white font-mono">

      {/* Header */}
      <div className="w-full flex justify-between items-center z-10">
        <div className="text-2xl font-bold tracking-widest text-cyan-400 glow-text">JARVIS</div>

        {/* HUD Stats */}
        <div className="flex gap-4 text-xs font-bold tracking-wider">
          <div className="flex flex-col items-end">
            <span className="text-cyan-600">CPU</span>
            <div className="w-24 h-2 bg-gray-800 rounded-full mt-1 overflow-hidden">
              <div className="h-full bg-cyan-500 transition-all duration-500" style={{ width: `${sysStats.cpu}%` }}></div>
            </div>
          </div>
          <div className="flex flex-col items-end">
            <span className="text-cyan-600">RAM</span>
            <div className="w-24 h-2 bg-gray-800 rounded-full mt-1 overflow-hidden">
              <div className="h-full bg-purple-500 transition-all duration-500" style={{ width: `${sysStats.ram}%` }}></div>
            </div>
          </div>
          <div className="flex flex-col items-end">
            <span className="text-cyan-600">PWR</span>
            <div className="w-24 h-2 bg-gray-800 rounded-full mt-1 overflow-hidden">
              <div className="h-full bg-green-500 transition-all duration-500" style={{ width: `${sysStats.battery}%` }}></div>
            </div>
          </div>
        </div>

        <div className="flex items-center text-sm ml-4">
          <span className={`status-indicator ${status !== 'offline' ? 'status-active' : 'status-inactive'}`}></span>
          {status.toUpperCase()}
        </div>
      </div>

      {/* Main Visualizer */}
      <div className="relative flex items-center justify-center w-64 h-64 md:w-96 md:h-96 my-8">
        {/* Outer Rings */}
        <div className={`absolute w-full h-full border border-cyan-500/30 rounded-full animate-[spin-slow_10s_linear_infinite]`}></div>
        <div className={`absolute w-[80%] h-[80%] border border-cyan-400/20 rounded-full animate-[spin-slow_15s_linear_infinite_reverse]`}></div>

        {/* Core */}
        <div
          onClick={() => ws.current.send(JSON.stringify({ action: "listen" }))}
          className={`
          w-40 h-40 rounded-full bg-cyan-500/10 backdrop-blur-md border border-cyan-400/50 flex items-center justify-center transition-all duration-300 cursor-pointer hover:bg-cyan-500/20
          ${status === 'listening' ? 'scale-110 shadow-[0_0_50px_rgba(0,255,255,0.6)]' : 'shadow-[0_0_20px_rgba(0,255,255,0.2)]'}
          ${status === 'offline' ? 'grayscale opacity-50' : ''}
        `}>
          <div className={`w-32 h-32 rounded-full bg-cyan-400/20 flex items-center justify-center animate-pulse`}>
            <div className="w-4 h-4 bg-white rounded-full shadow-[0_0_10px_white]"></div>
          </div>
        </div>

        {/* Helper Text */}
        <div className="absolute -bottom-16 text-cyan-500/50 text-xs tracking-widest uppercase">
          {status === 'listening' ? 'Listening...' : 'Click Orb or Press Ctrl+Space'}
        </div>
      </div>

      {/* Transcript Area */}
      <div className="w-full max-w-2xl min-h-[100px] bg-black/40 backdrop-blur-sm rounded-lg border border-white/10 p-4 mb-8 overflow-hidden">
        {transcript.length === 0 && <div className="text-gray-500 text-center italic">Waiting for command...</div>}
        {transcript.map((msg, i) => (
          <div key={i} className={`mb-2 ${msg.role === 'jarvis' ? 'text-cyan-300 text-right' : 'text-gray-300 text-left'}`}>
            <span className="text-xs opacity-50 mr-2">{msg.role.toUpperCase()}</span>
            {msg.text}
          </div>
        ))}
      </div>

      {/* Text Input */}
      <div className="w-full max-w-2xl mt-8 flex items-center gap-2">
        <input
          type="text"
          placeholder="Type a command..."
          className="flex-1 bg-black/40 border border-cyan-500/30 rounded px-4 py-3 text-white outline-none focus:border-cyan-400 focus:shadow-[0_0_15px_rgba(0,255,255,0.3)] transition-all placeholder:text-gray-600"
          onKeyDown={(e) => {
            if (e.key === 'Enter' && e.target.value.trim()) {
              sendCommand(e.target.value)
              e.target.value = ''
            }
          }}
        />
        <button className="px-6 py-3 bg-cyan-500/20 border border-cyan-500/50 rounded hover:bg-cyan-500/40 transition-all font-bold tracking-wider">
          SEND
        </button>
      </div>

    </div>
  )
}

export default App
