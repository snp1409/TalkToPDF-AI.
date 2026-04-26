import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
// FIXED: Added 'History' to the import list below!
import { 
  Upload, Send, FileText, Bot, User, Loader2, Plus, 
  Sparkles, CheckCircle2, LogOut, MessageSquare, Trash2, AlertCircle, History 
} from 'lucide-react';

export default function App() {
  // --- 1. STATE DEFINITIONS ---
  const [userName, setUserName] = useState('');
  const [tempName, setTempName] = useState('');
  const [sessions, setSessions] = useState([]); 
  const [currentFilename, setCurrentFilename] = useState('');
  const[chatHistory, setChatHistory] = useState([]);
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [isProcessed, setIsProcessed] = useState(false);
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef(null);

  const API_BASE_URL = "https://talktopdf-backend-moyx.onrender.com";

  // --- 2. SUGGESTION LIST ---
  const suggestions =[
    "Give me a detailed summary of this document.", 
    "Identify the key technical details or experiences mentioned.",
    "List all names, dates, and contact details you can find.",
    "What is the primary objective or purpose of this file?"
  ];

  // --- 3. MOUNT & IDENTITY LOGIC ---
  useEffect(() => {
    const savedUser = localStorage.getItem('chatUser');
    if (savedUser) setUserName(savedUser);
  },[]);

  const fetchUserSessions = async (name) => {
    const activeUser = name || userName;
    if (!activeUser) return;
    try {
      const res = await axios.get(`${API_BASE_URL}/sessions/${activeUser}`);
      setSessions(res.data?.sessions ||[]);
    } catch (err) { 
      setSessions([]); 
    }
  };

  useEffect(() => {
    if (userName) fetchUserSessions();
  }, [userName]);

  // --- 4. ACTION HANDLERS ---

  const handleLogin = (e) => {
    e.preventDefault();
    if (tempName.trim()) {
      localStorage.setItem('chatUser', tempName);
      setUserName(tempName);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('chatUser');
    setUserName('');
    setSessions([]);
    setChatHistory([]);
    setCurrentFilename('');
    setIsProcessed(false);
    window.location.reload();
  };

  const loadHistory = async (fname) => {
    if (!fname) return;
    setLoading(true);
    setChatHistory([]);
    setCurrentFilename(fname);
    setIsProcessed(true);
    try {
      const res = await axios.get(`${API_BASE_URL}/history/${userName}/${fname}`);
      setChatHistory(res.data?.history || []);
    } catch (err) { 
      setChatHistory([]);
    } finally { 
      setLoading(false); 
    }
  };

  const handleDelete = async (e, fname) => {
    e.stopPropagation();
    if (!window.confirm(`Delete ${fname}?`)) return;
    try {
      await axios.delete(`${API_BASE_URL}/delete/${userName}/${fname}`);
      setSessions(prev => prev.filter(f => f !== fname));
      if (currentFilename === fname) {
        setChatHistory([]);
        setCurrentFilename('');
        setIsProcessed(false);
      }
    } catch (err) { alert("Delete failed."); }
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    const payload = new FormData(); 
    payload.append('file', file);
    payload.append('username', userName);
    try {
      await axios.post(`${API_BASE_URL}/upload`, payload);
      setCurrentFilename(file.name);
      setIsProcessed(true);
      fetchUserSessions();
    } catch (err) { 
      alert("Upload failed."); 
    } finally { 
      setUploading(false); 
    }
  };

  const sendMessage = async (queryText) => {
    const q = queryText || question;
    if (!q || !q.trim() || loading) return;
    
    setChatHistory(prev => [...prev, { role: 'user', text: q }]);
    setLoading(true);
    setQuestion('');

    try {
      const payload = new FormData(); 
      payload.append('question', q);
      payload.append('username', userName);
      payload.append('filename', currentFilename || "None");
      
      const res = await axios.post(`${API_BASE_URL}/chat`, payload, { timeout: 60000 });
      setChatHistory(prev =>[...prev, { role: 'bot', text: res.data?.answer || "AI could not process that." }]);
    } catch (err) {
      setChatHistory(prev =>[...prev, { role: 'bot', text: "❌ Connection error." }]);
    } finally { 
      setLoading(false); 
    }
  };

  // Auto-scroll
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatHistory, loading]);

  // --- 5. RENDER LOGIC ---

  if (!userName) {
    return (
      <div className="h-screen flex items-center justify-center bg-[#0f172a] font-sans p-4">
        <div className="bg-white p-12 rounded-[2rem] shadow-2xl w-full max-w-md text-center">
          <Bot size={48} className="text-blue-600 mx-auto mb-4" />
          <h1 className="text-3xl font-bold mb-8 text-gray-800 tracking-tight">TalkToPDF AI</h1>
          <form onSubmit={handleLogin} className="space-y-4">
            <input type="text" placeholder="Enter Your Name" value={tempName} onChange={(e)=>setTempName(e.target.value)}
              className="w-full border-2 rounded-xl p-4 outline-none focus:border-blue-500 font-medium bg-gray-50 text-gray-700" />
            <button type="submit" className="w-full bg-blue-600 hover:bg-blue-700 text-white py-4 rounded-xl font-bold shadow-lg">Launch</button>
          </form>
          <p className="mt-8 text-[10px] text-gray-400 uppercase tracking-widest font-bold">Built for Suryanarayan Panda</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-[#F7F7F8] text-[#343541] overflow-hidden antialiased font-sans">
      
      {/* SIDEBAR */}
      <aside className="w-[280px] bg-[#202123] h-full flex flex-col p-3 text-white shadow-xl z-20">
        <div className="flex items-center justify-between mb-4 p-2">
           <span className="font-bold flex items-center gap-2 italic text-blue-400">TalkToPDF</span>
           <button onClick={handleLogout}><LogOut size={16} className="text-gray-500 hover:text-red-400 cursor-pointer"/></button>
        </div>
        <button onClick={() => {setChatHistory([]); setIsProcessed(false); setCurrentFilename(''); setFile(null);}} 
          className="w-full border border-white/10 p-3 rounded-md hover:bg-white/5 text-sm flex items-center gap-2 mb-4">
          <Plus size={14}/> New Chat
        </button>
        <div className="flex-1 overflow-y-auto space-y-1 custom-scrollbar">
          <p className="text-[10px] text-gray-500 font-bold uppercase mb-3 ml-2 flex items-center gap-2"><History size={12}/> History</p>
          {sessions.map((s, i) => (
            <div key={`session-${i}`} className="group flex items-center gap-1 pr-2">
              <button onClick={() => loadHistory(s)} 
                className={`flex-1 text-left p-2.5 rounded-md text-xs truncate flex items-center gap-2 ${currentFilename === s ? 'bg-[#343541] text-white' : 'text-gray-400 hover:bg-white/5'}`}>
                <MessageSquare size={14}/> {s}
              </button>
              <button onClick={(e) => handleDelete(e, s)} className="opacity-0 group-hover:opacity-100 p-2 text-gray-500 hover:text-red-500 transition-all">
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>
        <div className="mt-4 p-4 bg-[#2d2f35] rounded-xl border border-white/5">
           <input type="file" id="f-upload" hidden accept=".pdf" onChange={(e)=> {setFile(e.target.files[0]); setIsProcessed(false);}} />
           <label htmlFor="f-upload" className="cursor-pointer text-[10px] text-gray-400 block text-center border border-dashed border-gray-600 p-4 rounded-lg mb-2">
             {file ? <span className="text-blue-300 font-bold">{file.name}</span> : "Select PDF File"}
           </label>
           {file && !isProcessed && (
             <button onClick={handleUpload} disabled={uploading} className="w-full mt-2 bg-blue-600 py-1.5 rounded text-[10px] font-bold shadow-lg">
               {uploading ? "..." : "PROCESS"}
             </button>
           )}
           {isProcessed && <p className="text-[10px] text-green-400 font-bold text-center mt-2 animate-pulse flex items-center justify-center gap-1"><CheckCircle2 size={12}/> AI READY</p>}
        </div>
      </aside>

      {/* MAIN CHAT */}
      <main className="flex-1 flex flex-col bg-white relative">
        <div className="flex-1 overflow-y-auto pb-48 custom-scrollbar">
          {chatHistory.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center p-6">
               <Sparkles className="text-blue-600 mb-6 opacity-40" size={64} />
               <h1 className="text-4xl font-extrabold text-gray-800 italic mb-2 tracking-tight text-center">TalkToPDF</h1>
               <p className="text-gray-600 mt-2 max-w-md text-lg font-medium text-center italic">Welcome, <span className="text-blue-600 font-bold">{userName}</span></p>
               <p className="text-gray-400 mt-1 text-sm text-center">Upload or select a document to begin.</p>
            </div>
          ) : (
            chatHistory.map((msg, idx) => (
              <div key={`chat-${idx}`} className={`py-10 flex justify-center border-b border-gray-50 ${msg.role === 'bot' ? 'bg-[#F7F7F8]' : 'bg-white'}`}>
                <div className="max-w-3xl w-full flex gap-6 px-6 lg:px-0">
                  <div className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 shadow-sm ${msg.role === 'user' ? 'bg-blue-600 text-white' : 'bg-[#10a37f] text-white'}`}>
                    {msg.role === 'user' ? <User size={18}/> : <Bot size={18}/>}
                  </div>
                  <div className="markdown-content text-[16px] leading-relaxed text-[#343541] w-full overflow-hidden pt-0.5">
                    <ReactMarkdown>{msg.text}</ReactMarkdown>
                  </div>
                </div>
              </div>
            ))
          )}
          {loading && <div className="py-10 text-center text-gray-400 text-xs animate-pulse font-bold italic">AI IS THINKING...</div>}
          <div ref={chatEndRef} />
        </div>

        {/* INPUT, SUGGESTIONS & FOOTER */}
        <div className="absolute bottom-0 left-0 w-full bg-gradient-to-t from-white via-white to-transparent pt-10 pb-8 px-6">
           <div className="max-w-3xl mx-auto">
             
             {/* --- SUGGESTION BUBBLES ARE BACK --- */}
             {isProcessed && chatHistory.length === 0 && (
                <div className="flex flex-wrap gap-2 mb-6 justify-center animate-in fade-in slide-in-from-bottom-2">
                  {suggestions.map((s, i) => (
                    <button key={`sug-${i}`} onClick={() => sendMessage(s)} className="text-[10px] font-bold border border-gray-200 bg-white hover:bg-gray-100 px-4 py-2 rounded-full text-gray-600 shadow-sm transition-all">
                      {s}
                    </button>
                  ))}
                </div>
             )}

             <form onSubmit={(e) => {e.preventDefault(); sendMessage();}} className="relative flex items-center bg-white border-2 border-gray-100 rounded-2xl shadow-2xl p-1.5 focus-within:border-blue-500 transition-all">
                <input 
                  type="text" value={question} onChange={(e)=>setQuestion(e.target.value)} 
                  placeholder="Ask me anything..." 
                  className="flex-1 bg-transparent px-4 py-3 text-sm outline-none" 
                />
                <button type="submit" disabled={!question.trim() || loading} 
                  className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-100 text-white p-2.5 rounded-xl transition-all active:scale-95 shadow-md">
                  <Send size={20}/>
                </button>
             </form>
             <p className="text-[9px] text-gray-400 text-center mt-4 uppercase tracking-widest flex items-center justify-center gap-1 font-medium">
               <AlertCircle size={10}/> Private Session: {currentFilename || "Global Chat"}
             </p>
           </div>
        </div>
      </main>
    </div>
  );
}