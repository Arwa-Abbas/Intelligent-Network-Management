# NexoOps - Complete Setup Guide

## 🚀 Features

### ✅ Implemented Features:
1. **Real-time Network Monitoring**
   - Background monitoring every 5 seconds
   - CPU, Memory, Disk, Network metrics
   - Historical data storage (last 1000 entries)

2. **ChatOps Capabilities**
   - Natural language understanding (ML-based)
   - Conversational AI (greetings, thanks, etc.)
   - Network diagnostics commands
   - Log analysis integration

3. **Network Operations**
   - Network status monitoring
   - Active connections tracking
   - Network interface information
   - Bandwidth usage calculation
   - Speed test integration
   - Ping host functionality
   - Port checking
   - **Subnet scanning** (NEW!)

4. **Alert Management**
   - Real-time alert generation
   - 24-hour alert history
   - Severity-based filtering
   - Alert logging

5. **Log Analysis**
   - TF-IDF based summarization
   - ML-based severity classification
   - **Historical log storage** (NEW!)
   - **Time-based log retrieval** (NEW!)
   - "Summarize last N hours" support

6. **Enhanced UI**
   - Animated loading screen
   - Robot avatar in chat
   - Expandable chat window
   - Icon-based responses
   - Real-time analytics dashboard

---

## 📋 Prerequisites

- Python 3.8+
- Node.js 16+ (for React frontend)
- pip (Python package manager)
- npm (Node package manager)

---

## 🔧 Installation

### Step 1: Backend Setup

```bash
# Create project directory
mkdir nexoops-dashboard
cd nexoops-dashboard

# Create and activate virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Download NLTK data
python -c "import nltk; nltk.download('punkt')"
```

### Step 2: Frontend Setup

```bash
# In a separate terminal
npx create-react-app nexoops-frontend
cd nexoops-frontend

# Install additional dependencies
npm install framer-motion lucide-react recharts

# Copy App.js to src/App.js
```

### Step 3: File Structure

```
nexoops-dashboard/
├── api.py                  # Backend API
├── chatbot.py             # ChatOps logic
├── summarizer.py          # Log summarization
├── alert_classifier.py    # Alert classification
├── requirements.txt       # Python dependencies
├── network_logs.txt       # Auto-generated log storage
├── intent_model.joblib    # Auto-generated ML model
├── intent_vectorizer.joblib # Auto-generated vectorizer
└── alert_model.joblib     # Auto-generated classifier

nexoops-frontend/
└── src/
    └── App.js             # React frontend
```

---

## ▶️ Running the Application

### Terminal 1: Start Backend

```bash
# Activate virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Run Flask server
python api.py
```

**Expected Output:**
```
============================================================
NexoOps Backend API Server
============================================================

Available Endpoints:
...
Starting server on http://127.0.0.1:5000
============================================================
 * Running on http://127.0.0.1:5000
```

### Terminal 2: Start Frontend

```bash
cd nexoops-frontend
npm start
```

**Expected Output:**
```
Compiled successfully!
You can now view nexoops-frontend in the browser.
  Local:            http://localhost:3000
```

### Terminal 3: View Logs (Optional)

```bash
tail -f network_logs.txt
```

---

## 🎯 Usage Examples

### Conversational Queries
```
"Hi"
"Hello, how are you?"
"Thanks for your help"
"Bye"
```

### Network Status
```
"Show network status"
"What's my current bandwidth?"
"How is my network doing?"
```

### Diagnostics
```
"Diagnose high latency"
"Run speed test"
"System health check"
```

### Network Operations
```
"Ping 8.8.8.8"
"Ping google.com"
"Check port 192.168.1.1:80"
"Show network interfaces"
"Show active connections"
```

### Subnet Scanning (NEW!)
```
"Scan subnet 192.168.1.0/24"
"Discover hosts on 192.168.1.0/24"
"Find devices on my network"
```

### Historical Logs (NEW!)
```
"Summarize last hour of logs"
"Show logs from last 2 hours"
"What happened in the past 3 hours?"
```

### Alert Management
```
"Show today's critical alerts"
"Current alerts"
"What alerts do I have?"
```

### Log Analysis
```
# Upload a log file in the Log Analysis tab, then:
"Summarize logs"
"Analyze this log file"
```

---

## 🔌 API Endpoints

### Log Analysis
- `POST /summarize` - Summarize log text
- `POST /classify` - Classify log severity
- `POST /analyze` - Complete analysis

### ChatBot
- `POST /chat` - Chat with assistant

### Network Monitoring
- `GET /network/status` - Current status
- `GET /network/alerts` - Alert history
- `POST /network/speed-test` - Run speed test
- `GET /network/interfaces` - List interfaces
- `GET /network/connections` - Active connections
- `GET /network/bandwidth` - Bandwidth usage
- `POST /network/ping` - Ping a host
- `POST /network/port-check` - Check port
- `GET /network/health` - System health
- `GET /network/history` - Historical data

### Utility
- `POST /train-model` - Retrain ML models
- `GET /stats` - API statistics
- `GET /` - Health check

---

## 🎨 UI Features

### Loading Screen
- Animated security shield
- Progress bar with gradient
- System initialization steps

### Dashboard
- Three-panel layout (Control Panel, Main Content, System Metrics)
- Tab-based navigation (Logs, ChatOps, Analytics)
- Real-time updates
- Responsive design

### ChatOps Interface
- **Animated robot avatar** with:
  - Floating head animation
  - Blinking eyes
  - Antenna with pulsing light
  - Online status indicator
- Icon-based responses
- Expandable chat window
- Typing indicator
- Auto-scroll to latest messages

### Analytics
- Log line counts
- Critical keyword frequency
- Severity distribution charts
- Confidence levels

---

## 🔍 Troubleshooting

### Backend Issues

**Problem:** Model not found error
```
Solution: Run python alert_classifier.py to train the model first
```

**Problem:** Permission denied on network operations
```
Solution: Run with appropriate permissions (may need sudo on Linux)
```

**Problem:** Port 5000 already in use
```
Solution: Change port in api.py or kill existing process
```

### Frontend Issues

**Problem:** CORS errors
```
Solution: Ensure flask-cors is installed and CORS(app) is in api.py
```

**Problem:** Icons not rendering
```
Solution: Ensure lucide-react is installed: npm install lucide-react
```

---

## 📊 Performance Notes

- **Monitoring Interval:** 5 seconds
- **History Size:** 1000 entries (adjustable)
- **Log Storage:** 10,000 entries (adjustable)
- **Subnet Scan Limit:** 256 hosts max
- **Alert Retention:** 24 hours default

---

## 🔐 Security Considerations

1. **Network Access:** Backend has full network access
2. **Port Scanning:** Use responsibly on authorized networks only
3. **Log Storage:** Contains sensitive network information
4. **API Access:** No authentication (add for production)

---

## 🛠️ Customization

### Adjust Monitoring Interval
```python
# In chatbot.py, _monitor_loop function
time.sleep(5)  # Change to desired interval
```

### Change History Size
```python
# In chatbot.py, NetworkMonitor __init__
self.alert_history = deque(maxlen=1000)  # Adjust size
```

### Modify Alert Thresholds
```python
# In chatbot.py, check_system_health function
if cpu_percent > 85:  # Adjust threshold
```

---

## 📝 File Descriptions

### Backend Files

**api.py**
- Flask REST API server
- All endpoint definitions
- CORS configuration

**chatbot.py**
- Network monitoring class
- Intent classification (ML)
- Command handlers
- Log storage system

**summarizer.py**
- TF-IDF based summarization
- Clustering algorithm
- Pattern detection

**alert_classifier.py**
- Random Forest classifier
- Feature extraction
- Synthetic data generation

### Frontend Files

**App.js**
- React components
- UI animations
- API integration
- Icon rendering

---

## 🎓 Learning Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [React Documentation](https://react.dev/)
- [psutil Documentation](https://psutil.readthedocs.io/)
- [scikit-learn Documentation](https://scikit-learn.org/)
- [Framer Motion](https://www.framer.com/motion/)

---

## 📄 License

MIT License - Feel free to use and modify

---

## 🤝 Support

For issues or questions:
1. Check the troubleshooting section
2. Review API endpoint documentation
3. Check backend logs for errors
4. Verify all dependencies are installed

