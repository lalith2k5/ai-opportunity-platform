import { useState, useRef, useEffect } from 'react';
import { askAI, getChatHistory, getChatSession } from '../services/api';
import { Send, Loader2, Bot, User, History, Plus, MessageSquare, X } from 'lucide-react';

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
    setShowHistory(false);
  };

  return (
    <div className="flex h-screen bg-canvas">

      {/* History sidebar */}
      {showHistory && (
        <>
          <div className="fixed inset-0 bg-black/40 z-30 md:hidden" onClick={() => setShowHistory(false)} />
          <aside className="w-72 border-r border-edge bg-surface flex flex-col z-40 md:relative md:z-auto fixed inset-y-0 left-0">
            <div className="px-3.5 py-3 border-b border-edge flex items-center justify-between">
              <div className="flex items-center gap-2">
                <History size={14} className="text-ink-3" />
                <h2 className="text-xs font-medium text-ink uppercase tracking-wider">Sessions</h2>
              </div>
              <button onClick={() => setShowHistory(false)} className="p-1 rounded text-ink-4 hover:text-ink hover:bg-overlay">
                <X size={14} />
              </button>
            </div>

            <div className="p-3">
              <button onClick={newChat} className="btn-primary w-full text-xs py-2">
                <Plus size={13} /> New chat
              </button>
            </div>

            <div className="flex-1 overflow-y-auto px-2 pb-3">
              {sessions.length === 0 ? (
                <p className="text-xs text-ink-4 text-center py-6">No sessions yet</p>
              ) : (
                <div className="space-y-0.5">
                  {sessions.map(s => (
                    <button
                      key={s.id}
                      onClick={() => loadSession(s.id)}
                      className={`w-full text-left px-2.5 py-2 rounded-md transition-colors ${
                        sessionId === s.id
                          ? 'bg-accent/10 text-ink'
                          : 'text-ink-2 hover:bg-overlay'
                      }`}
                    >
                      <p className="text-xs truncate">{s.title || 'Untitled'}</p>
                      <p className="text-2xs text-ink-4 mt-0.5">
                        {new Date(s.created_at).toLocaleDateString()}
                      </p>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </aside>
        </>
      )}

      {/* Main chat */}
      <div className="flex flex-col flex-1 min-w-0">

        {/* Header */}
        <div className="border-b border-edge/60 px-6 py-4 glass flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-accent/10 flex items-center justify-center shadow-[inset_0_1px_0_0_rgb(255_255_255/0.05)]">
              <MessageSquare className="text-accent" size={18} />
            </div>
            <div>
              <h1 className="text-lg font-bold text-ink tracking-tight">AI Chat</h1>
              <p className="text-2xs text-ink-4 mt-0.5">Ask about opportunities, gaps, or trends</p>
            </div>
          </div>
          <button
            onClick={() => setShowHistory(h => !h)}
            className="btn-secondary text-xs"
          >
            <History size={13} /> {showHistory ? 'Hide' : 'History'}
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-auto p-6">
          {messages.length === 0 ? (
            <div className="max-w-2xl mx-auto mt-8 lg:mt-16">
              <div className="text-center mb-8">
                <div className="w-14 h-14 rounded-2xl bg-accent/10 flex items-center justify-center mx-auto mb-5 shadow-[inset_0_1px_0_0_rgb(255_255_255/0.05),0_8px_24px_-8px_rgb(var(--accent)/0.4)]">
                  <Bot className="text-accent" size={26} />
                </div>
                <h2 className="text-lg font-semibold text-ink tracking-tight">How can I help?</h2>
                <p className="text-sm text-ink-3 mt-1">Try one of these prompts to get started:</p>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                {SUGGESTIONS.map(s => (
                  <button
                    key={s}
                    onClick={() => send(s)}
                    className="text-left card card-hover p-4 text-sm text-ink-2"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="max-w-3xl mx-auto space-y-5">
              {messages.map((m, i) => (
                <div key={i} className={`flex gap-3 ${m.role === 'user' ? 'justify-end' : ''}`}>
                  {m.role === 'assistant' && (
                    <div className="w-8 h-8 rounded-lg bg-accent flex items-center justify-center flex-shrink-0 text-accent-fg shadow-[0_4px_12px_-2px_rgb(var(--accent)/0.55)]">
                      <Bot size={15} />
                    </div>
                  )}
                  <div className={`max-w-[80%] px-4 py-3 text-sm leading-relaxed ${
                    m.role === 'user'
                      ? 'bg-accent text-accent-fg rounded-2xl rounded-tr-md shadow-[0_4px_16px_-4px_rgb(var(--accent)/0.4)]'
                      : 'glass rounded-2xl rounded-tl-md text-ink-2'
                  }`}>
                    <p className="whitespace-pre-wrap">{m.content}</p>
                  </div>
                  {m.role === 'user' && (
                    <div className="w-7 h-7 rounded-md bg-overlay border border-edge flex items-center justify-center flex-shrink-0 text-ink-3">
                      <User size={14} />
                    </div>
                  )}
                </div>
              ))}
              {loading && (
                <div className="flex gap-3">
                  <div className="w-7 h-7 rounded-md bg-accent flex items-center justify-center text-accent-fg">
                    <Bot size={14} />
                  </div>
                  <div className="bg-surface border border-edge rounded-lg px-3.5 py-2.5">
                    <Loader2 className="animate-spin text-ink-4" size={14} />
                  </div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>
          )}
        </div>

        {/* Composer */}
        <div className="border-t border-edge/60 p-4 glass">
          <div className="max-w-3xl mx-auto flex gap-2">
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && send()}
              placeholder="Ask anything…"
              disabled={loading}
              className="input flex-1"
            />
            <button
              onClick={() => send()}
              disabled={loading || !input.trim()}
              className="btn-primary px-3.5"
            >
              <Send size={14} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
