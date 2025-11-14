import React, { useState } from "react";
import { motion } from "framer-motion";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";

function App() {
  const [logText, setLogText] = useState("");
  const [summary, setSummary] = useState("");
  const [classification, setClassification] = useState(null); // object now
  const [chatMessage, setChatMessage] = useState("");
  const [chatResponse, setChatResponse] = useState("");
  const [loading, setLoading] = useState(false);
  const [keywordCounts, setKeywordCounts] = useState([]); // top keywords

  const BACKEND_URL = "http://127.0.0.1:5000";

  // ---------------- Handle File Upload ----------------
  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = async (event) => {
        const content = event.target.result;
        setLogText(content);
        await processLog(content); // auto process after upload
      };
      reader.readAsText(file);
    }
  };

  // ---------------- Process Log: Summarize + Classify ----------------
  const processLog = async (text) => {
    if (!text) return;
    setLoading(true);
    try {
      // 1️⃣ Summarize
      const sumRes = await fetch(`${BACKEND_URL}/summarize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ log_text: text }),
      });
      const sumData = await sumRes.json();
      setSummary(sumData.summary);

      // Extract keywords for graph
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
        .slice(0,5); // top 5
      setKeywordCounts(sortedKeywords);

      // 2️⃣ Classify Alert (use summarized text)
      const classRes = await fetch(`${BACKEND_URL}/classify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ log_text: sumData.summary }),
      });
      const classData = await classRes.json();
      setClassification(classData.classification); // object with severity + probabilities
    } catch (err) {
      console.error(err);
      alert("Error processing log file");
    } finally {
      setLoading(false);
    }
  };

  // ---------------- Chatbot ----------------
  const handleChat = async () => {
    if (!chatMessage) return alert("Please enter a message");
    try {
      const response = await fetch(`${BACKEND_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: chatMessage }),
      });
      const data = await response.json();
      setChatResponse(data.response);
    } catch (err) {
      console.error(err);
      alert("Error sending message");
    }
  };

  // Prepare severity data for bar chart
  const severityData = classification && classification.probabilities
    ? Object.entries(classification.probabilities).map(([key, value]) => ({
        severity: key,
        probability: value
      }))
    : [];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-white p-8">
      <motion.h1
        className="text-4xl font-bold text-center mb-10 text-cyan-400 drop-shadow-lg"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        Intelligent Network Management Dashboard
      </motion.h1>

      <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-8">
        {/* ---------------- Log Upload & Summarization ---------------- */}
        <motion.section
          className="bg-gray-800/60 rounded-2xl p-6 shadow-lg border border-gray-700 hover:border-cyan-400 transition-all"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h2 className="text-2xl font-semibold mb-4 text-cyan-300">
            Upload & Process Log
          </h2>

          <input
            type="file"
            accept=".txt,.log"
            onChange={handleFileUpload}
            className="mb-3 block w-full text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-cyan-500 file:text-white hover:file:bg-cyan-600"
          />

          <textarea
            rows="6"
            value={logText}
            onChange={(e) => setLogText(e.target.value)}
            placeholder="Paste your network logs here or upload a log file"
            className="w-full p-3 rounded-lg bg-gray-900 text-white border border-gray-700 focus:outline-none focus:border-cyan-400 transition"
          />

          {loading && (
            <p className="mt-2 text-cyan-400 font-semibold">Processing...</p>
          )}

          {summary && (
            <motion.div
              className="mt-4 bg-gray-900 p-4 rounded-lg border border-gray-700"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
            >
              <h3 className="text-lg text-cyan-300 font-semibold mb-2">
                Summary:
              </h3>
              <pre className="whitespace-pre-wrap text-sm">{summary}</pre>

              <h3 className="text-lg text-cyan-300 font-semibold mt-4 mb-2">
                Alert Classification:
              </h3>
              <p className="text-yellow-300 font-semibold text-sm">
                {classification ? classification.severity : "N/A"}
              </p>

              {severityData.length > 0 && (
                <>
                  <h3 className="text-lg text-cyan-300 font-semibold mt-4 mb-2">
                    Severity Probabilities:
                  </h3>
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={severityData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="severity" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="probability" fill="#14B8A6" />
                    </BarChart>
                  </ResponsiveContainer>
                </>
              )}

              {keywordCounts.length > 0 && (
                <>
                  <h3 className="text-lg text-cyan-300 font-semibold mt-4 mb-2">
                    Top Keywords:
                  </h3>
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart layout="vertical" data={keywordCounts} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis type="number" />
                      <YAxis type="category" dataKey="keyword" />
                      <Tooltip />
                      <Bar dataKey="count" fill="#FACC15" />
                    </BarChart>
                  </ResponsiveContainer>
                </>
              )}
            </motion.div>
          )}
        </motion.section>

        {/* ---------------- Chatbot ---------------- */}
        <motion.section
          className="bg-gray-800/60 rounded-2xl p-6 shadow-lg border border-gray-700 hover:border-cyan-400 transition-all"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h2 className="text-2xl font-semibold mb-4 text-cyan-300">
            Network Chatbot
          </h2>
          <div className="flex flex-col sm:flex-row items-center gap-3">
            <input
              type="text"
              value={chatMessage}
              onChange={(e) => setChatMessage(e.target.value)}
              placeholder="Ask a question..."
              className="flex-1 p-3 rounded-lg bg-gray-900 text-white border border-gray-700 focus:outline-none focus:border-cyan-400 transition"
            />
            <button
              onClick={handleChat}
              className="w-full sm:w-auto bg-cyan-500 hover:bg-cyan-600 px-6 py-2 rounded-lg font-semibold transition-all"
            >
              Send
            </button>
          </div>

          {chatResponse && (
            <motion.div
              className="mt-4 bg-gray-900 p-4 rounded-lg border border-gray-700"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
            >
              <p>
                <strong className="text-cyan-400">Bot:</strong> {chatResponse}
              </p>
            </motion.div>
          )}
        </motion.section>
      </div>
    </div>
  );
}

export default App;
