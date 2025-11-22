# NexoOps: Intelligent Network Management System

### Computer Networks Project  
**Team Members:** Arwa Abbas | Mehwish Zehra | Areeza  

---

## 📌 Overview  
NexoOps is an **Intelligent Network Management System** that automates network monitoring using **AI, NLP, and Machine Learning**.  
It provides:

- Automatic log summarization  
- Automated alert severity classification  
- A ChatOps assistant for real-time network troubleshooting  

This system reduces manual work, improves troubleshooting speed, and increases network reliability.

---

## 🚀 Key Features

### 🔹 **1. Network Log Summarization**
- NLP-based extraction of key events  
- Detects anomalies, dropped connections, repeated errors  
- Generates short summaries for large logs  

### 🔹 **2. Automated Alert Classification**
- Severity levels: **Critical, High, Medium, Low**  
- Trained on:
  - Error codes  
  - Frequency  
  - Device source  
  - Message patterns  

### 🔹 **3. ChatOps Assistant**
Ask natural language queries:  
- “Show me today’s critical alerts”  
- “Summarize last hour logs”  
- “Show network status”  

All chatbot commands are listed in:  
📄 **chatops_commands.txt**

---

## Project Structure

```
NexoOps/
├── backend/
│ ├── data/
│ │ └── raw_logs/
│ │ ├── log1.txt
│ │ ├── log2_50K.txt
│ │ └── ... (all log files)
│ │
│ ├── src/
│ │ ├── alert_classifier.py
│ │ ├── api.py
│ │ ├── chatbot.py
│ │ ├── classifier.py
│ │ ├── preprocessing.py
│ │ ├── summarizer.py
│ │ ├── network_logs.txt
│ │ ├── alert_model.joblib
│ │ ├── intent_model.joblib
│ │ ├── intent_vectorizer.joblib
│ │ └── ...
│ │
│ ├── requirements.txt
│ 
├── frontend/
│ ├── react_app/
│ │ ├── src/
│ │ │ ├── App.js
│ │ │ ├── App.css
│ │ │ ├── index.js
│ │ │ ├── index.css
│ │ │ ├── components/
│ │ │ └── assets/
│ │ ├── package.json
│ │ ├── .gitignore
│ │ └── public/
│
| ── README.md
│
├── chatbot_commands.txt
└── README.md

```

## Project Setup


# ⚙️ Backend Setup (Python + Flask + ML Models)

### **1️⃣ Navigate to backend folder**
```bash
cd backend
```

### **2️⃣ Create Virtual Environment**
```bash
python -m venv venv
```

### **3️⃣ Activate Environment**
Windows:
```bash
venv\Scripts\activate
```
Mac/Linux:
```bash
source venv/bin/activate
```

### **4️⃣ Install Dependencies**
```bash
pip install -r requirements.txt
```

### **5️⃣ Navigate to src folder**
```bash
cd src
```

### **6️⃣ Run the backend server**
```bash
python api.py
```

# 🎨 Frontend Setup (React.js)

### **1️⃣ Navigate to react_app folder**
```bash
cd frontend/react_app
```

### **2️⃣ Install Node modules**
```bash
npm install
```


### **3️⃣ Run Frontend**
```bash
npm start
```



