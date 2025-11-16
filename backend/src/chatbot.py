import psutil
import speedtest
import socket
import subprocess
import platform
from datetime import datetime, timedelta
import time
import re
from summarizer import summarize_log
from alert_classifier import classify_log
import json
import threading
from collections import deque
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
import joblib
import os
import ipaddress

class LogStorage:
    """Store and retrieve network logs with timestamps"""
    def __init__(self, max_logs=10000):
        self.logs = deque(maxlen=max_logs)
        self.log_file = "network_logs.txt"
        self.load_logs()
    
    def add_log(self, log_entry):
        """Add a log entry with timestamp"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "content": log_entry
        }
        self.logs.append(entry)
        self.save_to_file(entry)
    
    def save_to_file(self, entry):
        """Persist logs to file"""
        try:
            with open(self.log_file, 'a') as f:
                f.write(f"[{entry['timestamp']}] {entry['content']}\n")
        except Exception as e:
            print(f"Error saving log: {e}")
    
    def load_logs(self):
        """Load logs from file on startup"""
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r') as f:
                    for line in f:
                        match = re.match(r'\[(.*?)\] (.*)', line)
                        if match:
                            self.logs.append({
                                "timestamp": match.group(1),
                                "content": match.group(2)
                            })
            except Exception as e:
                print(f"Error loading logs: {e}")
    
    def get_logs_by_time(self, hours=1):
        """Get logs from last N hours"""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_logs = []
        
        for log in self.logs:
            try:
                log_time = datetime.fromisoformat(log['timestamp'])
                if log_time > cutoff:
                    recent_logs.append(log)
            except:
                continue
        
        return recent_logs
    
    def get_all_logs_text(self, hours=None):
        """Get all logs as text"""
        if hours:
            logs = self.get_logs_by_time(hours)
        else:
            logs = list(self.logs)
        
        return "\n".join([f"[{log['timestamp']}] {log['content']}" for log in logs])

class NetworkMonitor:
    """Real-time network monitoring with historical data"""
    def __init__(self, history_size=1000):
        self.alert_history = deque(maxlen=history_size)
        self.network_stats_history = deque(maxlen=history_size)
        self.monitoring_active = False
        self.monitoring_thread = None
        self.log_storage = LogStorage()
        
    def start_monitoring(self):
        """Start background monitoring"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitoring_thread.start()
            self.log_storage.add_log("Network monitoring started")
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        self.monitoring_active = False
        self.log_storage.add_log("Network monitoring stopped")
        
    def _monitor_loop(self):
        """Background monitoring loop"""
        while self.monitoring_active:
            stats = self.get_system_network_stats()
            self.network_stats_history.append(stats)
            
            # Check for alerts
            alerts = self.check_system_health()
            for alert in alerts:
                self.alert_history.append(alert)
                self.log_storage.add_log(f"ALERT: [{alert['severity']}] {alert['type']} - {alert['message']}")
            
            time.sleep(5)
    
    def get_system_network_stats(self):
        """Get comprehensive network statistics"""
        try:
            net_io = psutil.net_io_counters()
            connections = psutil.net_connections()
            
            return {
                "timestamp": datetime.now().isoformat(),
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv,
                "errors_in": net_io.errin,
                "errors_out": net_io.errout,
                "drops_in": net_io.dropin,
                "drops_out": net_io.dropout,
                "active_connections": len([c for c in connections if c.status == 'ESTABLISHED']),
                "listening_ports": len([c for c in connections if c.status == 'LISTEN'])
            }
        except Exception as e:
            return {"error": str(e), "timestamp": datetime.now().isoformat()}
    
    def get_network_interfaces(self):
        """Get network interface information"""
        try:
            interfaces = psutil.net_if_addrs()
            interface_stats = psutil.net_if_stats()
            
            result = []
            for interface, addrs in interfaces.items():
                info = {
                    "name": interface,
                    "is_up": interface_stats[interface].isup if interface in interface_stats else False,
                    "speed_mbps": interface_stats[interface].speed if interface in interface_stats else 0,
                    "addresses": []
                }
                
                for addr in addrs:
                    info["addresses"].append({
                        "type": addr.family.name,
                        "address": addr.address,
                        "netmask": addr.netmask if hasattr(addr, 'netmask') else None
                    })
                
                result.append(info)
            
            return result
        except Exception as e:
            return {"error": str(e)}
    
    def scan_subnet(self, subnet_cidr, timeout=1):
        """Scan subnet for active hosts"""
        try:
            network = ipaddress.ip_network(subnet_cidr, strict=False)
            active_hosts = []
            
            # Limit to reasonable subnet size
            if network.num_addresses > 256:
                return {"error": "Subnet too large (max 256 hosts)"}
            
            self.log_storage.add_log(f"Starting subnet scan: {subnet_cidr}")
            
            for ip in network.hosts():
                ip_str = str(ip)
                try:
                    # Quick ping test
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(timeout)
                    result = sock.connect_ex((ip_str, 80))  # Try port 80
                    sock.close()
                    
                    if result == 0:
                        active_hosts.append({
                            "ip": ip_str,
                            "status": "active",
                            "port_80": "open"
                        })
                except:
                    pass
            
            self.log_storage.add_log(f"Subnet scan complete: {len(active_hosts)} hosts found")
            return active_hosts
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_active_connections(self, limit=20):
        """Get active network connections"""
        try:
            connections = psutil.net_connections()
            active_conns = []
            
            for conn in connections:
                if conn.status == 'ESTABLISHED':
                    active_conns.append({
                        "local_address": f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "N/A",
                        "remote_address": f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "N/A",
                        "status": conn.status,
                        "pid": conn.pid
                    })
            
            return active_conns[:limit]
        except Exception as e:
            return {"error": str(e)}
    
    def check_system_health(self):
        """Check system health and generate alerts"""
        alerts = []
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cpu_percent = psutil.cpu_percent(interval=0.5)
        if cpu_percent > 85:
            alerts.append({
                "timestamp": timestamp,
                "severity": "Critical" if cpu_percent > 95 else "High",
                "type": "CPU",
                "message": f"High CPU usage: {cpu_percent}%"
            })
        
        memory = psutil.virtual_memory()
        if memory.percent > 85:
            alerts.append({
                "timestamp": timestamp,
                "severity": "Critical" if memory.percent > 95 else "High",
                "type": "Memory",
                "message": f"High memory usage: {memory.percent}%"
            })
        
        net_io = psutil.net_io_counters()
        if net_io.errin > 100 or net_io.errout > 100:
            alerts.append({
                "timestamp": timestamp,
                "severity": "Medium",
                "type": "Network",
                "message": f"Network errors detected: IN({net_io.errin}) OUT({net_io.errout})"
            })
        
        disk = psutil.disk_usage('/')
        if disk.percent > 85:
            alerts.append({
                "timestamp": timestamp,
                "severity": "High",
                "type": "Disk",
                "message": f"High disk usage: {disk.percent}%"
            })
        
        return alerts
    
    def ping_host(self, host):
        """Ping a host"""
        try:
            param = "-n" if platform.system().lower() == "windows" else "-c"
            command = ["ping", param, "4", host]
            
            result = subprocess.run(command, capture_output=True, text=True, timeout=10)
            
            self.log_storage.add_log(f"Ping {host}: {'Success' if result.returncode == 0 else 'Failed'}")
            
            return {
                "success": result.returncode == 0,
                "host": host,
                "output": result.stdout
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "host": host, "error": "Timeout"}
        except Exception as e:
            return {"success": False, "host": host, "error": str(e)}
    
    def check_port(self, host, port):
        """Check if port is open"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()
            
            status = "open" if result == 0 else "closed"
            self.log_storage.add_log(f"Port check {host}:{port} - {status}")
            
            return {
                "host": host,
                "port": port,
                "open": result == 0
            }
        except Exception as e:
            return {"host": host, "port": port, "error": str(e)}
    
    def run_speed_test(self):
        """Run internet speed test"""
        try:
            self.log_storage.add_log("Speed test started")
            st = speedtest.Speedtest()
            st.get_best_server()
            
            download = st.download() / 1_000_000
            upload = st.upload() / 1_000_000
            ping = st.results.ping
            
            self.log_storage.add_log(f"Speed test complete: {download:.2f} Mbps down, {upload:.2f} Mbps up")
            
            return {
                "download_mbps": round(download, 2),
                "upload_mbps": round(upload, 2),
                "ping_ms": round(ping, 2),
                "server": st.results.server['name']
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_bandwidth_usage(self):
        """Calculate bandwidth usage from history"""
        if len(self.network_stats_history) < 2:
            return {"error": "Not enough data"}
        
        recent = self.network_stats_history[-1]
        older = self.network_stats_history[-2]
        
        time_diff = (datetime.fromisoformat(recent['timestamp']) - 
                    datetime.fromisoformat(older['timestamp'])).total_seconds()
        
        if time_diff == 0:
            return {"error": "Invalid time difference"}
        
        download_bps = (recent['bytes_recv'] - older['bytes_recv']) / time_diff
        upload_bps = (recent['bytes_sent'] - older['bytes_sent']) / time_diff
        
        return {
            "download_mbps": round(download_bps / 1_000_000, 2),
            "upload_mbps": round(upload_bps / 1_000_000, 2),
            "timestamp": recent['timestamp']
        }
    
    def get_recent_alerts(self, severity=None, hours=24):
        """Get recent alerts"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        alerts = []
        for alert in self.alert_history:
            alert_time = datetime.strptime(alert['timestamp'], "%Y-%m-%d %H:%M:%S")
            if alert_time > cutoff_time:
                if severity is None or alert['severity'] == severity:
                    alerts.append(alert)
        
        return alerts

class IntentClassifier:
    """ML-based intent classification"""
    def __init__(self):
        self.model_path = "intent_model.joblib"
        self.vectorizer_path = "intent_vectorizer.joblib"
        self.model = None
        self.vectorizer = None
        self.intents = [
            "network_status", "alerts", "speed_test", "ping", "port_check",
            "diagnose_latency", "log_summary", "bandwidth", "interfaces",
            "connections", "help", "system_health", "subnet_scan", "historical_logs",
            "greeting", "thanks", "goodbye"
        ]
        self.load_or_train_model()
    
    def load_or_train_model(self):
        """Load existing model or train new one"""
        if os.path.exists(self.model_path) and os.path.exists(self.vectorizer_path):
            self.model = joblib.load(self.model_path)
            self.vectorizer = joblib.load(self.vectorizer_path)
        else:
            self.train_model()
    
    def train_model(self):
        """Train intent classification model"""
        training_data = [
            # Greetings
            ("hi", "greeting"), ("hello", "greeting"), ("hey", "greeting"),
            ("good morning", "greeting"), ("good afternoon", "greeting"),
            
            # Thanks
            ("thanks", "thanks"), ("thank you", "thanks"), ("appreciate it", "thanks"),
            
            # Goodbye
            ("bye", "goodbye"), ("goodbye", "goodbye"), ("see you", "goodbye"),
            
            # Network status
            ("show network status", "network_status"),
            ("what is my network status", "network_status"),
            ("network overview", "network_status"),
            ("how is my network", "network_status"),
            
            # Alerts
            ("show today's critical alerts", "alerts"),
            ("current alerts", "alerts"),
            ("what alerts do I have", "alerts"),
            ("show alerts", "alerts"),
            
            # Speed test
            ("run speed test", "speed_test"),
            ("test my internet speed", "speed_test"),
            ("check internet speed", "speed_test"),
            ("how fast is my internet", "speed_test"),
            
            # Ping
            ("ping 8.8.8.8", "ping"),
            ("check connectivity to google.com", "ping"),
            ("is 192.168.1.1 reachable", "ping"),
            ("ping server", "ping"),
            
            # Port check
            ("check port 80 on 192.168.1.1", "port_check"),
            ("is port 443 open", "port_check"),
            ("port scan", "port_check"),
            
            # Latency
            ("diagnose high latency", "diagnose_latency"),
            ("network is slow", "diagnose_latency"),
            ("why is my network lagging", "diagnose_latency"),
            ("network performance issues", "diagnose_latency"),
            
            # Log summary
            ("summarize logs", "log_summary"),
            ("analyze log file", "log_summary"),
            ("what happened in the logs", "log_summary"),
            
            # Historical logs
            ("summarize last hour of logs", "historical_logs"),
            ("show logs from last 2 hours", "historical_logs"),
            ("what happened in the past hour", "historical_logs"),
            ("recent network logs", "historical_logs"),
            
            # Bandwidth
            ("show bandwidth usage", "bandwidth"),
            ("current bandwidth", "bandwidth"),
            ("network usage", "bandwidth"),
            
            # Interfaces
            ("show network interfaces", "interfaces"),
            ("list interfaces", "interfaces"),
            ("network adapters", "interfaces"),
            
            # Connections
            ("show active connections", "connections"),
            ("list connections", "connections"),
            ("who is connected", "connections"),
            
            # Subnet scan
            ("scan subnet 192.168.1.0/24", "subnet_scan"),
            ("discover hosts on network", "subnet_scan"),
            ("find devices on subnet", "subnet_scan"),
            
            # System health
            ("system health check", "system_health"),
            ("check system resources", "system_health"),
            ("how is system doing", "system_health"),
            
            # Help
            ("help", "help"),
            ("what can you do", "help"),
            ("commands", "help")
        ]
        
        texts, labels = zip(*training_data)
        
        self.vectorizer = TfidfVectorizer(max_features=100, ngram_range=(1, 2))
        X = self.vectorizer.fit_transform(texts)
        
        self.model = MultinomialNB()
        self.model.fit(X, labels)
        
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.vectorizer, self.vectorizer_path)
    
    def classify(self, message):
        """Classify user intent"""
        X = self.vectorizer.transform([message.lower()])
        intent = self.model.predict(X)[0]
        confidence = max(self.model.predict_proba(X)[0])
        
        return intent, confidence

class NetworkChatbot:
    """Main chatbot class"""
    def __init__(self):
        self.monitor = NetworkMonitor()
        self.monitor.start_monitoring()
        self.intent_classifier = IntentClassifier()
        self.user_name = None
    
    def extract_ip(self, message):
        """Extract IP address from message"""
        pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
        ips = re.findall(pattern, message)
        return ips[0] if ips else None
    
    def extract_subnet(self, message):
        """Extract subnet CIDR from message"""
        pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}/[0-9]{1,2}\b'
        subnets = re.findall(pattern, message)
        return subnets[0] if subnets else None
    
    def extract_port(self, message):
        """Extract port number from message"""
        pattern = r':(\d+)|port\s+(\d+)'
        matches = re.findall(pattern, message)
        if matches:
            return int(matches[0][0] or matches[0][1])
        return None
    
    def extract_hours(self, message):
        """Extract hour count from message"""
        patterns = [
            r'last\s+(\d+)\s+hour',
            r'past\s+(\d+)\s+hour',
            r'(\d+)\s+hour.*ago'
        ]
        for pattern in patterns:
            match = re.search(pattern, message.lower())
            if match:
                return int(match.group(1))
        
        if 'last hour' in message.lower() or 'past hour' in message.lower():
            return 1
        
        return None
    
    def handle_greeting(self):
        """Handle greeting"""
        greetings = [
            "Hello! I'm your NexoOps AI Assistant. How can I help you today?",
            "Hi there! Ready to help with your network management needs.",
            "Hey! What can I do for you today?",
            "Greetings! I'm here to assist with network operations."
        ]
        import random
        return f"[ICON:wave] {random.choice(greetings)}"
    
    def handle_thanks(self):
        """Handle thanks"""
        responses = [
            "You're welcome! Happy to help!",
            "Glad I could assist!",
            "Anytime! Let me know if you need anything else.",
            "My pleasure!"
        ]
        import random
        return f"[ICON:smile] {random.choice(responses)}"
    
    def handle_goodbye(self):
        """Handle goodbye"""
        return "[ICON:wave] Goodbye! Feel free to reach out anytime you need network assistance."
    
    def handle_network_status(self):
        """Handle network status request"""
        stats = self.monitor.get_system_network_stats()
        bandwidth = self.monitor.get_bandwidth_usage()
        
        response = "[ICON:activity] Network Status Report\n\n"
        
        if "error" not in stats:
            response += f"[ICON:wifi] Active Connections: {stats['active_connections']}\n"
            response += f"[ICON:server] Listening Ports: {stats['listening_ports']}\n"
            response += f"[ICON:upload] Data Sent: {stats['bytes_sent'] // (1024*1024)} MB\n"
            response += f"[ICON:download] Data Received: {stats['bytes_recv'] // (1024*1024)} MB\n"
            
            if stats['errors_in'] > 0 or stats['errors_out'] > 0:
                response += f"\n[ICON:alert-triangle] Errors: IN({stats['errors_in']}) OUT({stats['errors_out']})\n"
        
        if "error" not in bandwidth:
            response += f"\n[ICON:trending-up] Current Bandwidth:\n"
            response += f"Download: {bandwidth['download_mbps']} Mbps\n"
            response += f"Upload: {bandwidth['upload_mbps']} Mbps\n"
        
        return response
    
    def handle_alerts(self, severity=None):
        """Handle alerts request"""
        alerts = self.monitor.get_recent_alerts(severity=severity, hours=24)
        
        if not alerts:
            return "[ICON:check-circle] No critical alerts in the last 24 hours. System running normally."
        
        response = f"[ICON:alert-triangle] Critical Alerts (Last 24 Hours): {len(alerts)}\n\n"
        
        for alert in alerts[-10:]:
            icon = "[ICON:alert-circle]" if alert['severity'] == "Critical" else "[ICON:alert-triangle]"
            response += f"{icon} [{alert['severity']}] {alert['timestamp']}\n"
            response += f"   Type: {alert['type']} - {alert['message']}\n\n"
        
        return response
    
    def handle_speed_test(self):
        """Handle speed test request"""
        response = "[ICON:loader] Running speed test... This may take a moment.\n\n"
        
        result = self.monitor.run_speed_test()
        
        if "error" in result:
            return f"[ICON:x-circle] Speed test failed: {result['error']}"
        
        response = "[ICON:zap] Speed Test Results:\n\n"
        response += f"[ICON:download] Download: {result['download_mbps']} Mbps\n"
        response += f"[ICON:upload] Upload: {result['upload_mbps']} Mbps\n"
        response += f"[ICON:activity] Ping: {result['ping_ms']} ms\n"
        response += f"[ICON:server] Server: {result['server']}\n"
        
        if result['download_mbps'] < 10:
            response += "\n[ICON:alert-triangle] Warning: Download speed below average\n"
        if result['ping_ms'] > 100:
            response += "[ICON:alert-triangle] Warning: High latency detected\n"
        
        return response
    
    def handle_ping(self, message):
        """Handle ping request"""
        ip = self.extract_ip(message)
        if not ip:
            words = message.split()
            for word in words:
                if '.' in word and not word[0].isdigit():
                    ip = word
                    break
        
        if not ip:
            return "[ICON:help-circle] Please specify an IP address or hostname.\nExample: 'ping 8.8.8.8' or 'ping google.com'"
        
        result = self.monitor.ping_host(ip)
        
        if result['success']:
            return f"[ICON:check-circle] Host {ip} is reachable\n\nResponse:\n{result['output']}"
        else:
            error = result.get('error', 'Host unreachable')
            return f"[ICON:x-circle] Host {ip} is unreachable\nError: {error}"
    
    def handle_port_check(self, message):
        """Handle port check request"""
        ip = self.extract_ip(message)
        port = self.extract_port(message)
        
        if not ip or not port:
            return "[ICON:help-circle] Please specify both IP and port.\nExample: 'check port 192.168.1.1:80'"
        
        result = self.monitor.check_port(ip, port)
        
        if "error" in result:
            return f"[ICON:x-circle] Port check failed: {result['error']}"
        
        if result['open']:
            return f"[ICON:unlock] Port {port} on {ip} is OPEN"
        else:
            return f"[ICON:lock] Port {port} on {ip} is CLOSED"
    
    def handle_subnet_scan(self, message):
        """Handle subnet scanning"""
        subnet = self.extract_subnet(message)
        
        if not subnet:
            return "[ICON:help-circle] Please specify a subnet in CIDR notation.\nExample: 'scan subnet 192.168.1.0/24'"
        
        response = f"[ICON:loader] Scanning subnet {subnet}...\n\n"
        hosts = self.monitor.scan_subnet(subnet)
        
        if isinstance(hosts, dict) and "error" in hosts:
            return f"[ICON:x-circle] Scan failed: {hosts['error']}"
        
        response = f"[ICON:search] Subnet Scan Results for {subnet}\n\n"
        response += f"[ICON:check-circle] Active Hosts Found: {len(hosts)}\n\n"
        
        for host in hosts[:20]:
            response += f"[ICON:server] {host['ip']} - {host['status']}\n"
        
        if len(hosts) > 20:
            response += f"\n... and {len(hosts) - 20} more hosts\n"
        
        return response
    
    def handle_diagnose_latency(self):
        """Handle latency diagnosis"""
        response = "[ICON:activity] Network Latency Diagnosis\n\n"
        
        local_result = self.monitor.ping_host("192.168.1.1")
        if local_result['success']:
            response += "[ICON:check-circle] Local network: Healthy\n"
        else:
            response += "[ICON:x-circle] Local network: Issue detected\n"
        
        internet_result = self.monitor.ping_host("8.8.8.8")
        if internet_result['success']:
            response += "[ICON:check-circle] Internet connectivity: Good\n"
        else:
            response += "[ICON:x-circle] Internet connectivity: Issue detected\n"
        
        bandwidth = self.monitor.get_bandwidth_usage()
        if "error" not in bandwidth:
            response += f"\n[ICON:trending-up] Current Bandwidth:\n"
            response += f"Download: {bandwidth['download_mbps']} Mbps\n"
            response += f"Upload: {bandwidth['upload_mbps']} Mbps\n"
        
        if not local_result['success'] or not internet_result['success']:
            response += "\n[ICON:tool] Recommendations:\n"
            response += "- Check router connectivity\n"
            response += "- Restart network devices\n"
            response += "- Verify cable connections\n"
            response += "- Contact ISP if issues persist\n"
        
        return response
    
    def handle_log_summary(self, log_text):
        """Handle log summarization"""
        if not log_text:
            return "[ICON:file-text] Please provide log content to summarize. Upload a file or paste logs in the Log Analysis tab."
        
        summary = summarize_log(log_text)
        classification = classify_log(log_text)
        
        response = "[ICON:brain] Log Analysis Summary\n\n"
        response += f"Severity: {classification['severity']}\n\n"
        response += f"Summary:\n{summary}\n"
        
        return response
    
    def handle_historical_logs(self, message):
        """Handle historical log requests"""
        hours = self.extract_hours(message)
        if hours is None:
            hours = 1
        
        logs_text = self.monitor.log_storage.get_all_logs_text(hours=hours)
        
        if not logs_text:
            return f"[ICON:file-text] No logs found for the last {hours} hour(s)."
        
        summary = summarize_log(logs_text)
        classification = classify_log(logs_text)
        
        response = f"[ICON:clock] Network Logs Summary (Last {hours} Hour(s))\n\n"
        response += f"[ICON:alert-triangle] Severity: {classification['severity']}\n\n"
        response += f"[ICON:file-text] Summary:\n{summary}\n\n"
        response += f"Total log entries: {len(logs_text.split(chr(10)))}\n"
        
        return response
    
    def handle_bandwidth(self):
        """Handle bandwidth request"""
        bandwidth = self.monitor.get_bandwidth_usage()
        
        if "error" in bandwidth:
            return f"[ICON:alert-circle] Unable to calculate bandwidth: {bandwidth['error']}"
        
        response = "[ICON:trending-up] Current Bandwidth Usage\n\n"
        response += f"[ICON:download] Download: {bandwidth['download_mbps']} Mbps\n"
        response += f"[ICON:upload] Upload: {bandwidth['upload_mbps']} Mbps\n"
        response += f"[ICON:clock] Measured at: {bandwidth['timestamp']}\n"
        
        return response
    
    def handle_interfaces(self):
        """Handle network interfaces request"""
        interfaces = self.monitor.get_network_interfaces()
        
        if isinstance(interfaces, dict) and "error" in interfaces:
            return f"[ICON:x-circle] Error: {interfaces['error']}"
        
        response = f"[ICON:wifi] Network Interfaces ({len(interfaces)} found)\n\n"
        
        for iface in interfaces:
            status = "[ICON:check-circle]" if iface['is_up'] else "[ICON:x-circle]"
            response += f"{status} {iface['name']}\n"
            response += f"   Status: {'UP' if iface['is_up'] else 'DOWN'}\n"
            if iface['speed_mbps'] > 0:
                response += f"   Speed: {iface['speed_mbps']} Mbps\n"
            
            for addr in iface['addresses']:
                response += f"   {addr['type']}: {addr['address']}\n"
            response += "\n"
        
        return response
    
    def handle_connections(self):
        """Handle active connections request"""
        connections = self.monitor.get_active_connections(limit=15)
        
        if isinstance(connections, dict) and "error" in connections:
            return f"[ICON:x-circle] Error: {connections['error']}"
        
        response = f"[ICON:link] Active Connections ({len(connections)})\n\n"
        
        for conn in connections[:10]:
            response += f"[ICON:arrow-right] {conn['local_address']} -> {conn['remote_address']}\n"
            response += f"   PID: {conn['pid']}\n\n"
        
        if len(connections) > 10:
            response += f"... and {len(connections) - 10} more connections\n"
        
        return response
    
    def handle_system_health(self):
        """Handle system health check"""
        cpu = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        response = "[ICON:heart] System Health Check\n\n"
        
        cpu_icon = "[ICON:check-circle]" if cpu < 80 else "[ICON:alert-triangle]"
        response += f"{cpu_icon} CPU Usage: {cpu}%\n"
        
        mem_icon = "[ICON:check-circle]" if memory.percent < 80 else "[ICON:alert-triangle]"
        response += f"{mem_icon} Memory Usage: {memory.percent}%\n"
        
        disk_icon = "[ICON:check-circle]" if disk.percent < 80 else "[ICON:alert-triangle]"
        response += f"{disk_icon} Disk Usage: {disk.percent}%\n"
        
        net_stats = self.monitor.get_system_network_stats()
        if "error" not in net_stats:
            net_icon = "[ICON:check-circle]" if net_stats['errors_in'] < 100 else "[ICON:alert-triangle]"
            response += f"{net_icon} Network Errors: {net_stats['errors_in']} in / {net_stats['errors_out']} out\n"
        
        return response
    
    def handle_help(self):
        """Handle help request"""
        return """[ICON:help-circle] Network ChatOps Assistant - Available Commands

[ICON:wave] Conversation
• "Hi" / "Hello" - Greet me
• "Thanks" - You're welcome!
• "Bye" - Say goodbye

[ICON:activity] Network Diagnostics
• "Show network status" - Current network statistics
• "Diagnose high latency" - Network performance analysis
• "Run speed test" - Internet connection speed
• "Show bandwidth usage" - Current bandwidth metrics
• "System health check" - Overall system health

[ICON:alert-triangle] Alert Management
• "Show today's critical alerts" - View recent alerts
• "Current alerts" - Real-time alert status

[ICON:wifi] Network Operations
• "Show network interfaces" - List all interfaces
• "Show active connections" - Current connections
• "Ping 8.8.8.8" - Check connectivity
• "Check port 192.168.1.1:80" - Verify port status
• "Scan subnet 192.168.1.0/24" - Discover hosts

[ICON:file-text] Log Analysis
• "Summarize logs" - Analyze uploaded logs
• "Summarize last hour of logs" - Recent network logs
• "Show logs from last 2 hours" - Historical logs

[ICON:info] Examples:
• "Hey, what's my network status?"
• "Show me today's alerts"
• "Ping google.com"
• "Scan subnet 192.168.1.0/24"
• "Summarize last 3 hours of logs"
• "Run a speed test"

Just ask me anything about your network!"""
    
    def process_message(self, message, log_context=""):
        """Main message processing"""
        intent, confidence = self.intent_classifier.classify(message)
        
        handlers = {
            "greeting": self.handle_greeting,
            "thanks": self.handle_thanks,
            "goodbye": self.handle_goodbye,
            "network_status": self.handle_network_status,
            "alerts": self.handle_alerts,
            "speed_test": self.handle_speed_test,
            "ping": lambda: self.handle_ping(message),
            "port_check": lambda: self.handle_port_check(message),
            "subnet_scan": lambda: self.handle_subnet_scan(message),
            "diagnose_latency": self.handle_diagnose_latency,
            "log_summary": lambda: self.handle_log_summary(log_context),
            "historical_logs": lambda: self.handle_historical_logs(message),
            "bandwidth": self.handle_bandwidth,
            "interfaces": self.handle_interfaces,
            "connections": self.handle_connections,
            "system_health": self.handle_system_health,
            "help": self.handle_help
        }
        
        handler = handlers.get(intent, self.handle_help)
        return handler()

_chatbot_instance = None

def get_chatbot():
    """Get or create chatbot instance"""
    global _chatbot_instance
    if _chatbot_instance is None:
        _chatbot_instance = NetworkChatbot()
    return _chatbot_instance

def chatbot_response(message, log_context=""):
    """Main entry point for chatbot"""
    bot = get_chatbot()
    return bot.process_message(message, log_context)

if __name__ == "__main__":
    bot = NetworkChatbot()
    
    print("Network ChatOps Assistant - Testing")
    print("=" * 50)
    
    test_queries = [
        "Hello",
        "Show network status",
        "Show today's critical alerts",
        "Diagnose high latency",
        "Run speed test",
        "Ping 8.8.8.8",
        "Scan subnet 192.168.1.0/24",
        "Summarize last hour of logs",
        "Show bandwidth usage",
        "Thanks",
        "Bye"
    ]
    
    for query in test_queries:
        print(f"\nUser: {query}")
        response = bot.process_message(query)
        print(f"Bot: {response}")
        print("-" * 50)