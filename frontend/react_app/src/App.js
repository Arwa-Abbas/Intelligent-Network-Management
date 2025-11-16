import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { MessageSquare, Upload, Activity, AlertTriangle, TrendingUp, Server, Zap, Send, FileText, BarChart3, Brain, Shield, Lock, Wifi, Database } from "lucide-react";

function App() {
  const [isLoading, setIsLoading] = useState(true);
  const [logText, setLogText] = useState("");
  const [summary, setSummary] = useState("");
  const [classification, setClassification] = useState(null);
  const [chatMessages, setChatMessages] = useState([
    { role: "bot", text: "Hello! I'm NexoOps AI Assistant. Upload logs or ask me about network issues." }
  ]);
  const [chatInput, setChatInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [keywordCounts, setKeywordCounts] = useState([]);
  const [activeTab, setActiveTab] = useState("logs");
  const [isTyping, setIsTyping] = useState(false);
  const chatEndRef = useRef(null);

  const BACKEND_URL = "http://127.0.0.1:5000";

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 3500);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages]);

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = async (event) => {
        const content = event.target.result;
        setLogText(content);
        await processLog(content);
      };
      reader.readAsText(file);
    }
  };

  const processLog = async (text) => {
    if (!text) return;
    setLoading(true);
    try {
      const sumRes = await fetch(`${BACKEND_URL}/summarize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ log_text: text }),
      });
      const sumData = await sumRes.json();
      setSummary(sumData.summary);

      const lines = text.split("\n").filter(l => l.trim() !== "");
      const criticalWords = ['error','fail','warning','timeout','critical','fatal','panic','crash','corruption','breach'];
      const counts = {};
      lines.forEach(line => {
        criticalWords.forEach(word => {
          if(line.toLowerCase().includes(word)){
            counts[word] = (counts[word] || 0) + 1;
          }
        });
      });
      const sortedKeywords = Object.entries(counts)
        .map(([key,value]) => ({ keyword: key, count: value }))
        .sort((a,b) => b.count - a.count)
        .slice(0,5);
      setKeywordCounts(sortedKeywords);

      const classRes = await fetch(`${BACKEND_URL}/classify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ log_text: sumData.summary }),
      });
      const classData = await classRes.json();
      setClassification(classData.classification);
    } catch (err) {
      console.error(err);
      alert("Error processing log file");
    } finally {
      setLoading(false);
    }
  };

  const handleChat = async () => {
    if (!chatInput.trim()) return;
    
    const userMessage = { role: "user", text: chatInput };
    setChatMessages(prev => [...prev, userMessage]);
    setChatInput("");
    setIsTyping(true);

    try {
      const response = await fetch(`${BACKEND_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: chatInput }),
      });
      const data = await response.json();
      
      setTimeout(() => {
        setIsTyping(false);
        setChatMessages(prev => [...prev, { role: "bot", text: data.response }]);
      }, 1000);
    } catch (err) {
      console.error(err);
      setIsTyping(false);
      setChatMessages(prev => [...prev, { 
        role: "bot", 
        text: "Error connecting to backend. Please ensure the server is running." 
      }]);
    }
  };

  const severityData = classification && classification.probabilities
    ? Object.entries(classification.probabilities).map(([key, value]) => ({
        severity: key,
        probability: (value * 100).toFixed(1)
      }))
    : [];

  if (isLoading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center overflow-hidden relative font-mono">
        <div className="absolute inset-0">
          <div className="absolute inset-0 opacity-10" style={{
            backgroundImage: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(6, 182, 212, 0.03) 2px, rgba(6, 182, 212, 0.03) 4px)',
          }}></div>
        </div>

        <motion.div
          className="absolute top-20 left-20 w-96 h-96 bg-cyan-500 rounded-full opacity-10"
          animate={{ scale: [1, 1.5, 1], x: [0, 100, 0] }}
          transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
          style={{ filter: 'blur(80px)' }}
        />
        <motion.div
          className="absolute bottom-20 right-20 w-96 h-96 bg-orange-500 rounded-full opacity-10"
          animate={{ scale: [1, 1.3, 1], x: [0, -100, 0] }}
          transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
          style={{ filter: 'blur(80px)' }}
        />

        <div className="relative z-10 text-center px-8">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ duration: 0.5, type: "spring" }}
            className="mb-8"
          >
            <div className="relative inline-block">
              <motion.div
                className="w-32 h-32 mx-auto relative"
                animate={{ rotate: 360 }}
                transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
              >
                <div className="absolute inset-0 border-4 border-cyan-500/30 rounded-full"></div>
                <div className="absolute inset-2 border-4 border-transparent border-t-cyan-500 rounded-full"></div>
                <div className="absolute inset-4 border-4 border-transparent border-r-orange-500 rounded-full"></div>
              </motion.div>
              
              <motion.div
                className="absolute inset-0 flex items-center justify-center"
                animate={{ scale: [1, 1.1, 1] }}
                transition={{ duration: 2, repeat: Infinity }}
              >
                <Shield className="w-12 h-12 text-cyan-400" />
              </motion.div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <h1 className="text-6xl font-bold mb-4 tracking-wider">
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-orange-500">
                NexoOps
              </span>
            </h1>
            <p className="text-cyan-400 text-sm mb-12 tracking-widest uppercase">
              Intelligent Network Management System
            </p>

            <div className="w-80 mx-auto mb-8">
              <div className="h-1 bg-gray-800 rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-gradient-to-r from-cyan-500 via-cyan-400 to-orange-500"
                  initial={{ width: 0 }}
                  animate={{ width: "100%" }}
                  transition={{ duration: 3, ease: "easeInOut" }}
                />
              </div>
            </div>

            <motion.p
              className="text-cyan-400 text-sm"
              animate={{ opacity: [0.5, 1, 0.5] }}
              transition={{ duration: 1.5, repeat: Infinity }}
            >
              Initializing Secure Connection...
            </motion.p>

            <div className="mt-12 flex justify-center gap-8">
              {[
                { icon: Lock, label: "Security", delay: 0.5 },
                { icon: Database, label: "Database", delay: 0.8 },
                { icon: Wifi, label: "Network", delay: 1.1 }
              ].map((item, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: item.delay }}
                  className="flex flex-col items-center gap-2"
                >
                  <motion.div
                    animate={{ y: [0, -5, 0] }}
                    transition={{ duration: 2, repeat: Infinity, delay: i * 0.2 }}
                  >
                    <item.icon className="w-6 h-6 text-cyan-500" />
                  </motion.div>
                  <span className="text-xs text-gray-500">{item.label}</span>
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: item.delay + 0.5 }}
                    className="w-2 h-2 bg-green-500 rounded-full"
                  />
                </motion.div>
              ))}
            </div>
          </motion.div>
        </div>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="min-h-screen bg-black text-white font-mono"
    >
      <motion.header
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        transition={{ type: "spring", stiffness: 100 }}
        className="border-b border-cyan-900/50 bg-gradient-to-r from-black via-gray-900 to-black backdrop-blur-sm sticky top-0 z-50"
      >
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="relative">
                <div className="absolute inset-0 bg-cyan-500 blur-xl opacity-50 animate-pulse"></div>
                <Zap className="w-8 h-8 text-cyan-400 relative" strokeWidth={2.5} />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-orange-500">
                  NexoOps
                </h1>
                <p className="text-xs text-cyan-600">Intelligent Network Management System</p>
              </div>
            </div>
            
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-2 px-4 py-2 bg-cyan-950/30 border border-cyan-800/50 rounded-lg">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-xs text-cyan-400">SYSTEM ONLINE</span>
              </div>
            </div>
          </div>
        </div>
      </motion.header>

      <div className="container mx-auto px-6 py-8">
        <div className="grid lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1 space-y-6">
            <motion.div 
              className="bg-gradient-to-br from-gray-900 to-black border border-cyan-900/50 rounded-xl p-4 shadow-2xl"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 }}
            >
              <h2 className="text-sm text-cyan-400 mb-4 flex items-center gap-2">
                <Activity className="w-4 h-4" />
                CONTROL PANEL
              </h2>
              <div className="space-y-2">
                {[
                  { id: "logs", icon: FileText, label: "Log Analysis" },
                  { id: "chat", icon: MessageSquare, label: "ChatOps" },
                  { id: "analytics", icon: BarChart3, label: "Analytics" }
                ].map((tab, idx) => (
                  <motion.button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.3 + idx * 0.1 }}
                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                      activeTab === tab.id
                        ? "bg-cyan-500/20 border border-cyan-500/50 text-cyan-400"
                        : "bg-gray-800/50 border border-gray-700/50 text-gray-400 hover:bg-gray-800 hover:text-cyan-400"
                    }`}
                  >
                    <tab.icon className="w-5 h-5" />
                    <span className="font-semibold">{tab.label}</span>
                  </motion.button>
                ))}
              </div>
            </motion.div>

            <motion.div 
              className="bg-gradient-to-br from-gray-900 to-black border border-cyan-900/50 rounded-xl p-4 shadow-2xl"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.4 }}
            >
              <h2 className="text-sm text-cyan-400 mb-4 flex items-center gap-2">
                <TrendingUp className="w-4 h-4" />
                SYSTEM METRICS
              </h2>
              <div className="space-y-4">
                {[
                  { label: "Uptime", value: "99.8%", color: "text-green-400" },
                  { label: "Alerts", value: classification ? "1 Active" : "0 Active", color: classification ? "text-orange-400" : "text-cyan-400" },
                  { label: "Logs Processed", value: logText ? "1" : "0", color: "text-cyan-400" }
                ].map((stat, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.5 + i * 0.1 }}
                    className="flex justify-between items-center"
                  >
                    <span className="text-gray-400 text-sm">{stat.label}</span>
                    <span className={`${stat.color} font-bold`}>{stat.value}</span>
                  </motion.div>
                ))}
              </div>
            </motion.div>

            {classification && (
              <motion.div 
                className="bg-gradient-to-br from-orange-950/30 to-black border border-orange-500/50 rounded-xl p-4 shadow-2xl"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
              >
                <div className="flex items-center gap-2 mb-3">
                  <AlertTriangle className="w-5 h-5 text-orange-500" />
                  <h3 className="text-sm text-orange-400 font-bold">ALERT STATUS</h3>
                </div>
                <div className="bg-black/50 rounded-lg p-3 border border-orange-800/30">
                  <div className="text-2xl font-bold text-orange-400 mb-1">
                    {classification.severity}
                  </div>
                  <div className="text-xs text-gray-400">Severity Level Detected</div>
                </div>
              </motion.div>
            )}
          </div>

          <div className="lg:col-span-2">
            <AnimatePresence mode="wait">
              {activeTab === "logs" && (
                <motion.div
                  key="logs"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  className="space-y-6"
                >
                  <div className="bg-gradient-to-br from-gray-900 to-black border border-cyan-900/50 rounded-xl p-6 shadow-2xl">
                    <h2 className="text-lg text-cyan-400 mb-4 flex items-center gap-2">
                      <Upload className="w-5 h-5" />
                      LOG FILE ANALYZER
                    </h2>
                    
                    <div className="mb-4">
                      <label className="block mb-2 text-sm text-gray-400">Upload Log File</label>
                      <div className="relative">
                        <input
                          type="file"
                          accept=".txt,.log"
                          onChange={handleFileUpload}
                          className="hidden"
                          id="file-upload"
                        />
                        <label
                          htmlFor="file-upload"
                          className="flex items-center justify-center gap-2 w-full p-4 bg-cyan-950/30 border-2 border-dashed border-cyan-800/50 rounded-lg cursor-pointer hover:border-cyan-600 hover:bg-cyan-950/50 transition-all"
                        >
                          <Upload className="w-5 h-5 text-cyan-400" />
                          <span className="text-cyan-400">Click to upload or drag and drop</span>
                        </label>
                      </div>
                    </div>

                    <div>
                      <label className="block mb-2 text-sm text-gray-400">Or paste logs directly</label>
                      <textarea
                        rows="8"
                        value={logText}
                        onChange={(e) => setLogText(e.target.value)}
                        placeholder="2024-11-16 10:23:45 ERROR: Connection timeout on port 8080"
                        className="w-full p-4 rounded-lg bg-black border border-cyan-900/50 text-cyan-100 focus:outline-none focus:border-cyan-500 transition font-mono text-sm resize-none"
                      />
                    </div>

                    {loading && (
                      <div className="mt-4 flex items-center gap-3 text-cyan-400">
                        <div className="w-5 h-5 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin"></div>
                        <span className="text-sm">Processing logs...</span>
                      </div>
                    )}
                  </div>

                  {summary && (
                    <motion.div
                      className="bg-gradient-to-br from-gray-900 to-black border border-cyan-900/50 rounded-xl p-6 shadow-2xl"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                    >
                      <h3 className="text-lg text-cyan-400 mb-4 flex items-center gap-2">
                        <Brain className="w-5 h-5" />
                        AI ANALYSIS SUMMARY
                      </h3>
                      <div className="bg-black/50 p-4 rounded-lg border border-cyan-900/30">
                        <pre className="whitespace-pre-wrap text-sm text-cyan-100">{summary}</pre>
                      </div>

                      {severityData.length > 0 && (
                        <div className="mt-6">
                          <h4 className="text-sm text-cyan-400 mb-3">SEVERITY DISTRIBUTION</h4>
                          <div className="bg-black/50 p-4 rounded-lg border border-cyan-900/30">
                            <ResponsiveContainer width="100%" height={250}>
                              <BarChart data={severityData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#0e7490" opacity={0.3} />
                                <XAxis dataKey="severity" stroke="#06b6d4" style={{ fontSize: '12px' }} />
                                <YAxis stroke="#06b6d4" style={{ fontSize: '12px' }} />
                                <Tooltip contentStyle={{ backgroundColor: '#000', border: '1px solid #06b6d4', borderRadius: '8px' }} />
                                <Bar dataKey="probability" fill="#06b6d4" radius={[8, 8, 0, 0]} />
                              </BarChart>
                            </ResponsiveContainer>
                          </div>
                        </div>
                      )}

                      {keywordCounts.length > 0 && (
                        <div className="mt-6">
                          <h4 className="text-sm text-cyan-400 mb-3">TOP CRITICAL KEYWORDS</h4>
                          <div className="bg-black/50 p-4 rounded-lg border border-cyan-900/30">
                            <ResponsiveContainer width="100%" height={200}>
                              <BarChart layout="vertical" data={keywordCounts}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#fb923c" opacity={0.2} />
                                <XAxis type="number" stroke="#fb923c" style={{ fontSize: '12px' }} />
                                <YAxis type="category" dataKey="keyword" stroke="#fb923c" style={{ fontSize: '12px' }} />
                                <Tooltip contentStyle={{ backgroundColor: '#000', border: '1px solid #fb923c', borderRadius: '8px' }} />
                                <Bar dataKey="count" fill="#fb923c" radius={[0, 8, 8, 0]} />
                              </BarChart>
                            </ResponsiveContainer>
                          </div>
                        </div>
                      )}
                    </motion.div>
                  )}
                </motion.div>
              )}

              {activeTab === "chat" && (
                <motion.div
                  key="chat"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  className="bg-gradient-to-br from-gray-900 to-black border border-cyan-900/50 rounded-xl shadow-2xl flex flex-col h-[calc(100vh-220px)]"
                >
                  <div className="p-4 border-b border-cyan-900/50">
                    <div className="flex items-center gap-3">
                      <motion.div
                        className="relative"
                        animate={{ y: [0, -3, 0] }}
                        transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                      >
                        <div className="w-12 h-12 bg-gradient-to-br from-cyan-500 to-cyan-700 rounded-full flex items-center justify-center relative overflow-hidden">
                          <Server className="w-7 h-7 text-white relative z-10" />
                          <motion.div
                            className="absolute inset-0 bg-gradient-to-t from-cyan-300/50 to-transparent"
                            animate={{ opacity: [0.3, 0.6, 0.3] }}
                            transition={{ duration: 2, repeat: Infinity }}
                          />
                        </div>
                        <motion.div
                          className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 rounded-full border-2 border-gray-900"
                          animate={{ scale: [1, 1.2, 1] }}
                          transition={{ duration: 1.5, repeat: Infinity }}
                        />
                      </motion.div>
                      <div>
                        <h3 className="text-cyan-400 font-bold">NexoOps AI Assistant</h3>
                        <p className="text-xs text-gray-500">Network Operations ChatOps</p>
                      </div>
                    </div>
                  </div>

                  <div className="flex-1 overflow-y-auto p-4 space-y-4">
                    {chatMessages.map((msg, idx) => (
                      <motion.div
                        key={idx}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                      >
                        <div className={`flex gap-2 max-w-[80%] ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}>
                          {msg.role === "bot" && (
                            <motion.div
                              className="w-8 h-8 bg-gradient-to-br from-cyan-500 to-cyan-700 rounded-full flex items-center justify-center flex-shrink-0"
                              animate={{ rotate: [0, 5, 0, -5, 0] }}
                              transition={{ duration: 3, repeat: Infinity }}
                            >
                              <Server className="w-5 h-5 text-white" />
                            </motion.div>
                          )}
                          <motion.div
                            initial={{ scale: 0.9 }}
                            animate={{ scale: 1 }}
                            className={`p-3 rounded-2xl ${
                              msg.role === "user"
                                ? "bg-cyan-600 text-white rounded-tr-none"
                                : "bg-gray-800 text-cyan-100 rounded-tl-none border border-cyan-900/50"
                            }`}
                          >
                            <p className="text-sm whitespace-pre-wrap">{msg.text}</p>
                          </motion.div>
                        </div>
                      </motion.div>
                    ))}

                    {isTyping && (
                      <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="flex justify-start"
                      >
                        <div className="flex gap-2 max-w-[80%]">
                          <div className="w-8 h-8 bg-gradient-to-br from-cyan-500 to-cyan-700 rounded-full flex items-center justify-center flex-shrink-0">
                            <Server className="w-5 h-5 text-white" />
                          </div>
                          <div className="p-3 rounded-2xl bg-gray-800 text-cyan-100 rounded-tl-none border border-cyan-900/50">
                            <div className="flex gap-1">
                              <motion.div
                                className="w-2 h-2 bg-cyan-400 rounded-full"
                                animate={{ y: [0, -5, 0] }}
                                transition={{ duration: 0.6, repeat: Infinity, delay: 0 }}
                              />
                              <motion.div
                                className="w-2 h-2 bg-cyan-400 rounded-full"
                                animate={{ y: [0, -5, 0] }}
                                transition={{ duration: 0.6, repeat: Infinity, delay: 0.2 }}
                              />
                              <motion.div
                                className="w-2 h-2 bg-cyan-400 rounded-full"
                                animate={{ y: [0, -5, 0] }}
                                transition={{ duration: 0.6, repeat: Infinity, delay: 0.4 }}
                              />
                            </div>
                          </div>
                        </div>
                      </motion.div>
                    )}
                    <div ref={chatEndRef} />
                  </div>

                  <div className="p-4 border-t border-cyan-900/50">
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={chatInput}
                        onChange={(e) => setChatInput(e.target.value)}
                        onKeyPress={(e) => e.key === "Enter" && handleChat()}
                        placeholder="Ask about network issues, logs, or diagnostics..."
                        className="flex-1 p-3 rounded-lg bg-black border border-cyan-900/50 text-cyan-100 focus:outline-none focus:border-cyan-500 transition text-sm"
                      />
                      <motion.button
                        onClick={handleChat}
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        className="px-6 py-3 bg-cyan-600 hover:bg-cyan-500 rounded-lg transition-all flex items-center gap-2 font-bold"
                      >
                        <Send className="w-4 h-4" />
                      </motion.button>
                    </div>
                  </div>
                </motion.div>
              )}

              {activeTab === "analytics" && (
                <motion.div
                  key="analytics"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  className="space-y-6"
                >
                  <div className="bg-gradient-to-br from-gray-900 to-black border border-cyan-900/50 rounded-xl p-6 shadow-2xl">
                    <h2 className="text-lg text-cyan-400 mb-4 flex items-center gap-2">
                      <Activity className="w-5 h-5" />
                      LOG ANALYSIS OVERVIEW
                    </h2>
                    
                    {!logText ? (
                      <div className="bg-black/50 p-8 rounded-lg border border-cyan-900/30 text-center">
                        <Upload className="w-16 h-16 text-cyan-400/50 mx-auto mb-4" />
                        <p className="text-gray-400 mb-2">No logs analyzed yet</p>
                        <p className="text-sm text-gray-500">Upload a log file in the Log Analysis tab to see analytics</p>
                      </div>
                    ) : (
                      <div className="space-y-6">
                        {/* Summary Stats Cards */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          <motion.div
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ delay: 0.1 }}
                            className="bg-black/50 p-4 rounded-lg border border-cyan-900/30"
                          >
                            <div className="flex items-center justify-between mb-2">
                              <span className="text-xs text-gray-400 uppercase">Total Lines</span>
                              <FileText className="w-4 h-4 text-cyan-400" />
                            </div>
                            <div className="text-2xl font-bold text-cyan-400">
                              {logText.split('\n').filter(l => l.trim()).length}
                            </div>
                          </motion.div>

                          <motion.div
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ delay: 0.2 }}
                            className="bg-black/50 p-4 rounded-lg border border-orange-900/30"
                          >
                            <div className="flex items-center justify-between mb-2">
                              <span className="text-xs text-gray-400 uppercase">Critical Keywords</span>
                              <AlertTriangle className="w-4 h-4 text-orange-400" />
                            </div>
                            <div className="text-2xl font-bold text-orange-400">
                              {keywordCounts.reduce((sum, item) => sum + item.count, 0)}
                            </div>
                          </motion.div>

                          <motion.div
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ delay: 0.3 }}
                            className="bg-black/50 p-4 rounded-lg border border-cyan-900/30"
                          >
                            <div className="flex items-center justify-between mb-2">
                              <span className="text-xs text-gray-400 uppercase">Alert Level</span>
                              <Shield className="w-4 h-4 text-cyan-400" />
                            </div>
                            <div className="text-2xl font-bold text-cyan-400">
                              {classification ? classification.severity : 'N/A'}
                            </div>
                          </motion.div>
                        </div>

                        {/* Combined Charts */}
                        {severityData.length > 0 && (
                          <div className="bg-black/50 p-4 rounded-lg border border-cyan-900/30">
                            <h3 className="text-sm text-cyan-400 mb-4 flex items-center gap-2">
                              <BarChart3 className="w-4 h-4" />
                              SEVERITY PROBABILITY DISTRIBUTION
                            </h3>
                            <ResponsiveContainer width="100%" height={300}>
                              <BarChart data={severityData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#0e7490" opacity={0.3} />
                                <XAxis dataKey="severity" stroke="#06b6d4" style={{ fontSize: '12px' }} />
                                <YAxis stroke="#06b6d4" style={{ fontSize: '12px' }} />
                                <Tooltip 
                                  contentStyle={{ 
                                    backgroundColor: '#000', 
                                    border: '1px solid #06b6d4',
                                    borderRadius: '8px'
                                  }}
                                  formatter={(value) => [`${value}%`, 'Probability']}
                                />
                                <Bar dataKey="probability" fill="#06b6d4" radius={[8, 8, 0, 0]}>
                                  {severityData.map((entry, index) => {
                                    const colors = {
                                      'Low': '#22c55e',
                                      'Medium': '#eab308',
                                      'High': '#f97316',
                                      'Critical': '#ef4444'
                                    };
                                    return (
                                      <motion.rect
                                        key={`bar-${index}`}
                                        initial={{ height: 0 }}
                                        animate={{ height: 'auto' }}
                                        transition={{ delay: index * 0.1 }}
                                        fill={colors[entry.severity] || '#06b6d4'}
                                      />
                                    );
                                  })}
                                </Bar>
                              </BarChart>
                            </ResponsiveContainer>
                          </div>
                        )}

                        {keywordCounts.length > 0 && (
                          <div className="bg-black/50 p-4 rounded-lg border border-cyan-900/30">
                            <h3 className="text-sm text-cyan-400 mb-4 flex items-center gap-2">
                              <TrendingUp className="w-4 h-4" />
                              CRITICAL KEYWORD FREQUENCY
                            </h3>
                            <ResponsiveContainer width="100%" height={300}>
                              <BarChart layout="vertical" data={keywordCounts}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#fb923c" opacity={0.2} />
                                <XAxis type="number" stroke="#fb923c" style={{ fontSize: '12px' }} />
                                <YAxis 
                                  type="category" 
                                  dataKey="keyword" 
                                  stroke="#fb923c" 
                                  style={{ fontSize: '12px' }}
                                  width={100}
                                />
                                <Tooltip 
                                  contentStyle={{ 
                                    backgroundColor: '#000', 
                                    border: '1px solid #fb923c',
                                    borderRadius: '8px'
                                  }}
                                  formatter={(value) => [value, 'Occurrences']}
                                />
                                <Bar dataKey="count" fill="#fb923c" radius={[0, 8, 8, 0]} />
                              </BarChart>
                            </ResponsiveContainer>
                          </div>
                        )}

                        {/* Detailed Breakdown */}
                        <div className="bg-black/50 p-4 rounded-lg border border-cyan-900/30">
                          <h3 className="text-sm text-cyan-400 mb-4">LOG FILE DETAILS</h3>
                          <div className="space-y-3 text-sm">
                            <div className="flex justify-between items-center py-2 border-b border-gray-800">
                              <span className="text-gray-400">Character Count</span>
                              <span className="text-cyan-400 font-mono">{logText.length}</span>
                            </div>
                            <div className="flex justify-between items-center py-2 border-b border-gray-800">
                              <span className="text-gray-400">Word Count</span>
                              <span className="text-cyan-400 font-mono">{logText.split(/\s+/).length}</span>
                            </div>
                            <div className="flex justify-between items-center py-2 border-b border-gray-800">
                              <span className="text-gray-400">Line Count</span>
                              <span className="text-cyan-400 font-mono">
                                {logText.split('\n').filter(l => l.trim()).length}
                              </span>
                            </div>
                            {classification && classification.probabilities && (
                              <div className="flex justify-between items-center py-2">
                                <span className="text-gray-400">Confidence Level</span>
                                <span className="text-cyan-400 font-mono">
                                  {Math.max(...Object.values(classification.probabilities)).toFixed(1)}%
                                </span>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

export default App;