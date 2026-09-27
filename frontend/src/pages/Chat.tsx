import { useState, useRef, useEffect } from 'react';
import { askAI, getChatHistory, getChatSession } from '../services/api';
import { Send, Loader2, Bot, User, History, Plus } from 'lucide-react';

interface Message { role: 'user' | 'assistant'; content: string; }
interface Session { id: number; title: string; created_at: string; messages?: Message[]; }

const SUGGESTIONS = [
  'What are the most promising AI opportunities in healthcare?',
  'Show me research gaps in cybersecurity.',
  'Suggest startup ideas in agriculture.',
  'Which technologies are growing rapidly?',
];

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<number | undefined>(undefined);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const loadHistory = () => {
    getChatHistory().then((d: Session[]) => setSessions(d)).catch(() => {});
  };

  useEffect(() => { loadHistory(); }, []);
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  const send = async (text?: string) => {
    const question = (text ?? input).trim();
    if (!question || loading) return;
    setMessages(m => [...m, { role: 'user', content: question }]);
    setInput(''); setLoading(true);
    try {
      const data = await askAI(question);
      setMessages(m => [...m, { role: 'assistant', content: data.response || 'No response' }]);
      if (data.session_id) setSessionId(data.session_id);
      loadHistory();
    } catch (e: any) {
      setMessages(m => [...m, { role: 'assistant', content: `Error: ${e.message}` }]);
    } finally { setLoading(false); }
  };

  const loadSession = async (id: number) => {
    try {
      const data = await getChatSession(id);
      setMessages(data.messages || []);
      setSessionId(id);
      setShowHistory(false);
    } catch (e) { console.error(e); }
  };

  const newChat = () => {
    setMessages([]);
    setSessionId(undefined);
  };

  return (
    <div className="flex h-screen">
      {showHistory && (
        <aside className="w-72 border-r border-brand-border bg-brand-panel p-4 overflow-auto">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-white font-semibold flex items-center gap-2">
              <History size={18} /> History
            </h2>
            <button
              onClick={() => setShowHistory(false)}
              className="text-gray-400 hover:text-white text-xs"
            >Close</button>
          </div>
          <button
            onClick={newChat}
            className="w-full mb-4 bg-brand-accent hover:bg-indigo-600 text-white py-2 rounded-lg flex items-center justify-center gap-2 text-sm"
          >
            <Plus size={16} /> New Chat
          </button>
          <div className="space-y-2">
            {sessions.length === 0 ? (
              <p className="text-xs text-gray-500 text-center py-4">No sessions yet</p>
            ) : (
              sessions.map(s => (
                <button
                  key={s.id}
                  onClick={() => loadSession(s.id)}
                  className={`w-full text-left p-3 rounded-lg text-xs transition-colors ${
                    sessionId === s.id ? 'bg-brand-accent text-white' : 'bg-brand-dark text-gray-300 hover:bg-brand-border'
                  }`}
                >
                  <p className="truncate">{s.title || 'Untitled'}</p>
                  <p className="text-gray-500 text-[10px] mt-1">
                    {new Date(s.created_at).toLocaleDateString()}
                  </p>
                </button>
              ))
            )}
          </div>
        </aside>
      )}

      <div className="flex flex-col flex-1">
        <div className="border-b border-brand-border p-4 bg-brand-panel flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">AI Chat</h1>
            <p className="text-sm text-gray-400 mt-0.5">Ask about opportunities, research gaps, or trends.</p>
          </div>
          <button
            onClick={() => setShowHistory(h => !h)}
            className="bg-brand-dark border border-brand-border hover:border-brand-accent text-white px-3 py-2 rounded-lg flex items-center gap-2 text-sm"
          >
            <History size={16} /> {showHistory ? 'Hide' : 'History'}
          </button>
        </div>

        <div className="flex-1 overflow-auto p-6">
          {messages.length === 0 ? (
            <div className="max-w-2xl mx-auto mt-12">
              <div className="text-center mb-8">
                <Bot className="mx-auto text-brand-accent mb-3" size={48} />
                <h2 className="text-xl font-semibold text-white">How can I help?</h2>
                <p className="text-gray-400 mt-1">Try one of these:</p>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {SUGGESTIONS.map(s => (
                  <button key={s} onClick={() => send(s)}
                    className="text-left bg-brand-panel border border-brand-border hover:border-brand-accent rounded-lg p-4 text-sm text-gray-300 transition-colors">
                    {s}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="max-w-3xl mx-auto space-y-4">
              {messages.map((m, i) => (
                <div key={i} className={`flex gap-3 ${m.role === 'user' ? 'justify-end' : ''}`}>
                  {m.role === 'assistant' && (
                    <div className="w-8 h-8 rounded-full bg-brand-accent flex items-center justify-center flex-shrink-0"><Bot size={18} /></div>
                  )}
                  <div className={`max-w-[80%] rounded-2xl px-4 py-3 ${m.role === 'user' ? 'bg-brand-accent text-white' : 'bg-brand-panel border border-brand-border text-gray-200'}`}>
                    <p className="whitespace-pre-wrap text-sm leading-relaxed">{m.content}</p>
                  </div>
                  {m.role === 'user' && (
                    <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center flex-shrink-0"><User size={18} /></div>
                  )}
                </div>
              ))}
              {loading && (
                <div className="flex gap-3">
                  <div className="w-8 h-8 rounded-full bg-brand-accent flex items-center justify-center"><Bot size={18} /></div>
                  <div className="bg-brand-panel border border-brand-border rounded-2xl px-4 py-3"><Loader2 className="animate-spin text-gray-400" size={18} /></div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>
          )}
        </div>

        <div className="border-t border-brand-border p-6 bg-brand-panel">
          <div className="max-w-3xl mx-auto flex gap-3">
            <input
              type="text" value={input} onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && send()}
              placeholder="Ask about opportunities, trends, research gaps..." disabled={loading}
              className="flex-1 bg-brand-dark border border-brand-border rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-brand-accent disabled:opacity-50"
            />
            <button onClick={() => send()} disabled={loading || !input.trim()}
              className="bg-brand-accent hover:bg-indigo-600 disabled:opacity-50 text-white px-5 rounded-lg flex items-center justify-center transition-colors">
              <Send size={18} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
