import React, { useState, useEffect, useRef } from 'react';

const getApiBase = () => {
  if (import.meta.env.VITE_API_URL) return import.meta.env.VITE_API_URL;
  return window.location.origin + "/api";
};

const getWsBase = () => {
  if (import.meta.env.VITE_WS_URL) return import.meta.env.VITE_WS_URL;
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}/ws`;
};

const API_BASE = getApiBase();
const WS_BASE = getWsBase();

export default function Chat() {
  const [me, setMe] = useState(null);
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState("");
  const ws = useRef(null);
  const chatRef = useRef(null);
  const target = me === "Alice" ? "Bob" : "Alice";

  useEffect(() => {
    if (!me) return;
    fetch(`${API_BASE}/messages/${me}/${target}`).then(r => r.json()).then(setMessages);
    let alive = true;
    const connect = () => {
      ws.current = new WebSocket(`${WS_BASE}/${me}`);
      ws.current.onmessage = (e) => {
        const msg = JSON.parse(e.data);
        setMessages(prev => {
          const match = prev.find(m => (msg._id && m._id === msg._id) || (msg.client_id && m.client_id === msg.client_id));
          return match ? prev.map(m => ((msg._id && m._id === msg._id) || (msg.client_id && m.client_id === msg.client_id)) ? { ...m, ...msg } : m) : [...prev, msg];
        });
      };
      ws.current.onclose = () => alive && setTimeout(connect, 2000);
    };
    connect();
    return () => { alive = false; ws.current?.close(); };
  }, [me]);

  useEffect(() => { chatRef.current?.scrollTo(0, chatRef.current.scrollHeight); }, [messages]);

  const send = () => {
    if (!text.trim() || !ws.current) return;
    const tempId = Date.now().toString();
    const msg = { sender: me, receiver: target, text, timestamp: new Date().toISOString(), _id: tempId, client_id: tempId, emotion: null, trust_score: null, is_sarcasm: null };
    setMessages(prev => [...prev, msg]);
    ws.current.send(JSON.stringify({ receiver: target, text, client_id: tempId }));
    setText("");
  };

  const aiText = (m) => {
    if (!m.emotion) return "analyzing...";
    if (m.is_sarcasm) return "😏 Sarcasm ⚠️";
    const map = { joy: "😊", anger: "😡", fear: "😨", sadness: "😢", neutral: "🙂", surprise: "😲" };
    const label = m.emotion.charAt(0).toUpperCase() + m.emotion.slice(1);
    return `${map[m.emotion] || "🙂"} ${label} · ${m.trust_score ?? 0}% trust`;
  };

  if (!me) return (
    <div className="app-container" style={{justifyContent: 'center', alignItems: 'center', gap: '20px'}}>
      <h1>Who are you?</h1>
      <div style={{display: 'flex', gap: '20px'}}>
        {["Alice", "Bob"].map(u => <button key={u} className="user-btn" onClick={() => setMe(u)}>{u}</button>)}
      </div>
    </div>
  );

  return (
    <div className="app-container">
      <div className="header">
        <strong>Chatting with {target}</strong>
        <button className="user-btn" onClick={() => setMe(null)}>Logout ({me})</button>
      </div>
      <div className="chat-window" ref={chatRef}>
        {messages.map(m => (
          <div key={m._id} className={`bubble ${m.sender === me ? 'sent' : 'received'}`}>
            <div className="text">{m.text}</div>
            <div className="meta">
              <span className="ai-info">{aiText(m)}</span>
              <span className="timestamp">{new Date(m.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
            </div>
          </div>
        ))}
      </div>
      <div className="input-area">
        <textarea value={text} onChange={e => setText(e.target.value)} 
          onKeyDown={e => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), send())}
          placeholder="Type a message..." rows="1" />
        <button className="send" onClick={send}>→</button>
      </div>
    </div>
  );
}
