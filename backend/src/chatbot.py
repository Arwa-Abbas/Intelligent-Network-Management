
import psutil
import socket
import subprocess
import platform
from datetime import datetime, timedelta
import time
import re
import threading
from collections import deque, Counter
import os
import ipaddress
import random
import struct
import json

# ML imports for log summarization
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.cluster import KMeans
    import numpy as np
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

try:
    import nltk
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False

# imports with fallbacks
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    import speedtest
    SPEEDTEST_AVAILABLE = True
except ImportError:
    SPEEDTEST_AVAILABLE = False

# Download NLTK data
if NLTK_AVAILABLE:
    try:
        nltk.download('punkt', quiet=True)
    except:
        pass


class LogSummarizer:
    """ML-powered log summarization for network logs"""
    
    def __init__(self):
        self.network_keywords = [
            'error', 'fail', 'timeout', 'warning', 'critical', 'alert',
            'connection', 'port', 'ping', 'dns', 'ssl', 'certificate',
            'bandwidth', 'latency', 'packet', 'drop', 'retry', 'refused',
            'unreachable', 'closed', 'open', 'scan', 'subnet', 'arp',
            'gateway', 'route', 'interface', 'adapter', 'throughput'
        ]
    
    def preprocess_logs(self, log_text):
        """Splits log text into non-empty lines."""
        lines = log_text.split('\n')
        sentences = [line.strip() for line in lines if line.strip()]
        return sentences
    
    def detect_network_patterns(self, sentences):
        """Detect repeated network-related error/warning patterns."""
        network_error_keywords = [
            'error', 'fail', 'timeout', 'warning', 'critical', 'alert',
            'connection lost', 'connection refused', 'unreachable',
            'port closed', 'ssl error', 'certificate', 'dns failed',
            'packet loss', 'bandwidth', 'latency', 'drop', 'retry',
            'scan complete', 'subnet scan', 'arp', 'gateway', 'route'
        ]
        
        # Filter lines containing network-related keywords
        relevant_lines = [line for line in sentences if any(
            kw in line.lower() for kw in network_error_keywords
        )]
        line_counts = Counter(relevant_lines)
        return line_counts
    
    def compute_tfidf_scores(self, sentences):
        """Compute TF-IDF scores for sentences with network-focused vocabulary."""
        if not ML_AVAILABLE or len(sentences) < 2:
            return None, None
            
        try:
            vectorizer = TfidfVectorizer(
                stop_words='english',
                max_features=1000,
                ngram_range=(1, 2)
            )
            tfidf_matrix = vectorizer.fit_transform(sentences)
            sentence_scores = np.array(tfidf_matrix.sum(axis=1)).ravel()
            return sentence_scores, tfidf_matrix
        except Exception as e:
            print(f"TF-IDF computation failed: {e}")
            return None, None
    
    def cluster_sentences(self, tfidf_matrix, sentences, num_clusters=5):
        """Cluster similar sentences using KMeans."""
        if not ML_AVAILABLE or tfidf_matrix is None or len(sentences) < 2:
            return {0: list(range(len(sentences)))}
            
        try:
            num_clusters = min(num_clusters, len(sentences), 10)
            if num_clusters < 2:
                return {0: list(range(len(sentences)))}
                
            kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=10)
            kmeans.fit(tfidf_matrix)
            
            clusters = {i: [] for i in range(num_clusters)}
            for idx, label in enumerate(kmeans.labels_):
                clusters[label].append(idx)
            return clusters
        except Exception as e:
            print(f"Clustering failed: {e}")
            return {0: list(range(len(sentences)))}
    
    def select_representatives(self, sentences, sentence_scores, clusters, line_counts):
        """Select representative sentences from each cluster."""
        rep_indices = []
        
        for cluster_id, indices in clusters.items():
            if not indices:
                continue
                
            cluster_scores = []
            for idx in indices:
                score = sentence_scores[idx] if sentence_scores is not None else 0
                
                # Boost network-critical lines
                line = sentences[idx].lower()
                if any(kw in line for kw in self.network_keywords):
                    score += 2.0
                if sentences[idx] in line_counts:
                    score += line_counts[sentences[idx]] * 0.5
                
                cluster_scores.append((score, idx))
            
            if cluster_scores:
                best_sentence_idx = max(cluster_scores)[1]
                rep_indices.append(best_sentence_idx)
        
        return rep_indices
    
    def rank_top_sentences(self, sentences, sentence_scores, line_counts, rep_indices, n_sentences=5):
        """Rank and select top sentences for summary."""
        if not rep_indices:
            return []
            
        final_scores = []
        for idx in rep_indices:
            score = sentence_scores[idx] if sentence_scores is not None else 0
            
            # Enhanced scoring for network logs
            line = sentences[idx].lower()
            
            # High priority for errors and critical events
            if any(word in line for word in ['error', 'fail', 'critical', 'alert']):
                score += 3.0
            elif any(word in line for word in ['warning', 'timeout', 'drop']):
                score += 2.0
            elif any(word in line for word in ['scan', 'ping', 'dns', 'ssl']):
                score += 1.0
            
            if sentences[idx] in line_counts:
                score += line_counts[sentences[idx]]
            
            final_scores.append((score, idx))
        
        # Sort by score descending
        final_scores.sort(reverse=True)
        
        # Pick top n_sentences
        top_indices = [idx for score, idx in final_scores[:n_sentences]]
        top_indices.sort()  # Maintain chronological order
        return top_indices
    
    def summarize_network_logs(self, log_text, n_sentences=8, num_clusters=5):
        """
        ML-powered summarization specifically for network logs.
        Falls back to simple extraction if ML libraries are unavailable.
        """
        sentences = self.preprocess_logs(log_text)
        
        # If few sentences or ML not available, use simple approach
        if len(sentences) <= n_sentences or not ML_AVAILABLE:
            return self._simple_network_summary(sentences, n_sentences)
        
        try:
            line_counts = self.detect_network_patterns(sentences)
            sentence_scores, tfidf_matrix = self.compute_tfidf_scores(sentences)
            
            if tfidf_matrix is None:
                return self._simple_network_summary(sentences, n_sentences)
            
            clusters = self.cluster_sentences(tfidf_matrix, sentences, num_clusters)
            rep_indices = self.select_representatives(sentences, sentence_scores, clusters, line_counts)
            top_indices = self.rank_top_sentences(sentences, sentence_scores, line_counts, rep_indices, n_sentences)
            
            summary_sentences = [sentences[i] for i in top_indices]
            return self._format_network_summary(summary_sentences, len(sentences))
            
        except Exception as e:
            print(f"ML summarization failed, using fallback: {e}")
            return self._simple_network_summary(sentences, n_sentences)
    
    def _simple_network_summary(self, sentences, n_sentences):
        """Fallback summary for when ML is not available."""
        # Prioritize network-related lines
        network_sentences = []
        other_sentences = []
        
        for sentence in sentences:
            if any(kw in sentence.lower() for kw in self.network_keywords):
                network_sentences.append(sentence)
            else:
                other_sentences.append(sentence)
        
        # Take network sentences first, then fill with others
        summary_sentences = network_sentences[:n_sentences]
        if len(summary_sentences) < n_sentences:
            summary_sentences.extend(other_sentences[:n_sentences - len(summary_sentences)])
        
        return self._format_network_summary(summary_sentences[:n_sentences], len(sentences))
    
    def _format_network_summary(self, summary_sentences, total_lines):
        """Format the summary with network-specific headers."""
        header = f"🔍 NETWORK LOGS SUMMARY ({len(summary_sentences)} key entries from {total_lines} total)\n"
        header += "━" * 50 + "\n\n"
        
        formatted_summary = header
        for i, sentence in enumerate(summary_sentences, 1):
            # Add icons based on content
            line_lower = sentence.lower()
            if any(word in line_lower for word in ['error', 'fail', 'critical']):
                icon = "🔴"
            elif any(word in line_lower for word in ['warning', 'timeout']):
                icon = "🟡"
            elif any(word in line_lower for word in ['success', 'complete', 'open']):
                icon = "🟢"
            elif any(word in line_lower for word in ['scan', 'ping', 'dns']):
                icon = "🔍"
            else:
                icon = "📝"
            
            formatted_summary += f"{icon} {sentence}\n"
        
        if not ML_AVAILABLE:
            formatted_summary += f"\n💡 Note: Basic summary mode (install scikit-learn and nltk for AI-powered summarization)"
        
        return formatted_summary


class LogStorage:
    """Persistent log storage with ML summarization"""
    
    def __init__(self, max_logs=10000):
        self.logs = deque(maxlen=max_logs)
        self.log_file = "network_logs.txt"
        self.uploaded_logs = ""
        self.summarizer = LogSummarizer()
        self._load_logs()
    
    def add(self, entry):
        log = {"timestamp": datetime.now().isoformat(), "content": entry}
        self.logs.append(log)
        self._save(log)
    
    def set_uploaded(self, text):
        self.uploaded_logs = text
        self.add(f"Uploaded {len(text.splitlines())} log lines")
    
    def get_uploaded(self):
        return self.uploaded_logs
    
    def _save(self, log):
        try:
            with open(self.log_file, 'a') as f:
                f.write(f"[{log['timestamp']}] {log['content']}\n")
        except: pass
    
    def _load_logs(self):
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r') as f:
                    for line in f:
                        m = re.match(r'\[(.*?)\] (.*)', line)
                        if m:
                            self.logs.append({"timestamp": m.group(1), "content": m.group(2)})
            except: pass
    
    def get_recent(self, hours=1):
        cutoff = datetime.now() - timedelta(hours=hours)
        result = []
        for log in self.logs:
            try:
                if datetime.fromisoformat(log['timestamp']) > cutoff:
                    result.append(log)
            except: pass
        return result
    
    def get_text(self, hours=None):
        logs = self.get_recent(hours) if hours else list(self.logs)
        return "\n".join([f"[{l['timestamp']}] {l['content']}" for l in logs])
    
    def summarize_logs(self, hours=24, use_ml=True):
        """Generate AI-powered summary of logs"""
        logs = self.get_recent(hours)
        if not logs:
            return f"📊 No logs found in the last {hours} hours."
        
        log_text = self.get_text(hours)
        
        if use_ml and ML_AVAILABLE:
            return self.summarizer.summarize_network_logs(log_text)
        else:
            return self._basic_summary(logs, hours)
    
    def _basic_summary(self, logs, hours):
        """Basic categorical summary without ML"""
        categories = {
            "🔴 Errors/Critical": 0,
            "🟡 Warnings": 0,
            "🔍 Scans & Tests": 0,
            "🌐 Connectivity": 0,
            "📊 Performance": 0,
            "⚡ System Operations": 0
        }
        
        recent_activities = []
        
        for log in logs[-20:]:  # Last 20 activities for recent context
            content = log['content'].lower()
            timestamp = log['timestamp']
            
            # Categorize
            if any(word in content for word in ['error', 'fail', 'critical']):
                categories["🔴 Errors/Critical"] += 1
            elif 'warning' in content:
                categories["🟡 Warnings"] += 1
            elif any(word in content for word in ['scan', 'ping', 'dns lookup']):
                categories["🔍 Scans & Tests"] += 1
            elif any(word in content for word in ['port', 'connection', 'website']):
                categories["🌐 Connectivity"] += 1
            elif any(word in content for word in ['speed', 'bandwidth', 'latency']):
                categories["📊 Performance"] += 1
            else:
                categories["⚡ System Operations"] += 1
            
            # Keep recent activities for display
            recent_activities.append(f"{timestamp[11:16]} - {log['content']}")
        
        # Generate summary
        summary = f"NETWORK LOGS SUMMARY (Last {hours} hours)\n"
        summary += "━" * 50 + "\n"
        summary += f"Total entries: {len(logs)}\n\n"
        
        summary += "ACTIVITY BREAKDOWN:\n"
        for category, count in categories.items():
            if count > 0:
                summary += f"  {category}: {count}\n"
        
        summary += f"\nRECENT ACTIVITIES ({len(recent_activities)} shown):\n"
        for activity in recent_activities[-10:]:
            summary += f"  • {activity}\n"
        
        if not ML_AVAILABLE:
            summary += f"\nTip: Install 'scikit-learn' and 'nltk' for AI-powered smart summarization"
        
        return summary


class NetworkOperations:
    """Core network operations - ALL REAL TRAFFIC"""
    
    def __init__(self):
        self.logs = LogStorage()
        self.stats_history = deque(maxlen=1000)
        self.alerts = deque(maxlen=500)
        self.is_windows = platform.system().lower() == "windows"
    
    # ═══════════════════════════════════════════════════════════════
    # SYSTEM STATS - Real psutil calls
    # ═══════════════════════════════════════════════════════════════
    
    def get_network_stats(self):
        """Get real network I/O statistics"""
        try:
            io = psutil.net_io_counters()
            conns = psutil.net_connections(kind='inet')
            return {
                "timestamp": datetime.now().isoformat(),
                "bytes_sent": io.bytes_sent,
                "bytes_recv": io.bytes_recv,
                "packets_sent": io.packets_sent,
                "packets_recv": io.packets_recv,
                "errors_in": io.errin,
                "errors_out": io.errout,
                "drops_in": io.dropin,
                "drops_out": io.dropout,
                "established": len([c for c in conns if c.status == 'ESTABLISHED']),
                "listening": len([c for c in conns if c.status == 'LISTEN']),
                "total_connections": len(conns)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_interfaces(self):
        """Get all network interfaces with details"""
        try:
            addrs = psutil.net_if_addrs()
            stats = psutil.net_if_stats()
            result = []
            for name, addresses in addrs.items():
                info = {
                    "name": name,
                    "is_up": stats[name].isup if name in stats else False,
                    "speed": stats[name].speed if name in stats else 0,
                    "mtu": stats[name].mtu if name in stats else 0,
                    "addresses": []
                }
                for addr in addresses:
                    info["addresses"].append({
                        "family": addr.family.name,
                        "address": addr.address,
                        "netmask": getattr(addr, 'netmask', None),
                        "broadcast": getattr(addr, 'broadcast', None)
                    })
                result.append(info)
            return result
        except Exception as e:
            return {"error": str(e)}
    
    def get_connections(self, limit=50):
        """Get active network connections"""
        try:
            conns = psutil.net_connections(kind='inet')
            result = []
            for c in conns:
                if c.status == 'ESTABLISHED':
                    try:
                        proc = psutil.Process(c.pid).name() if c.pid else "Unknown"
                    except:
                        proc = "Unknown"
                    result.append({
                        "local": f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else "N/A",
                        "remote": f"{c.raddr.ip}:{c.raddr.port}" if c.raddr else "N/A",
                        "status": c.status,
                        "pid": c.pid,
                        "process": proc
                    })
            return result[:limit]
        except Exception as e:
            return {"error": str(e)}
    
    def get_listening_ports(self):
        """Get all listening ports"""
        try:
            conns = psutil.net_connections(kind='inet')
            result = []
            for c in conns:
                if c.status == 'LISTEN':
                    try:
                        proc = psutil.Process(c.pid).name() if c.pid else "Unknown"
                    except:
                        proc = "Unknown"
                    result.append({
                        "address": c.laddr.ip if c.laddr else "0.0.0.0",
                        "port": c.laddr.port if c.laddr else 0,
                        "pid": c.pid,
                        "process": proc
                    })
            return sorted(result, key=lambda x: x['port'])
        except Exception as e:
            return {"error": str(e)}
    
    def get_process_network_usage(self):
        """Get network usage per process"""
        try:
            conns = psutil.net_connections(kind='inet')
            usage = {}
            for c in conns:
                if c.pid:
                    try:
                        proc = psutil.Process(c.pid)
                        name = proc.name()
                        if name not in usage:
                            usage[name] = {"pid": c.pid, "connections": 0, "established": 0, "listening": 0}
                        usage[name]["connections"] += 1
                        if c.status == 'ESTABLISHED':
                            usage[name]["established"] += 1
                        elif c.status == 'LISTEN':
                            usage[name]["listening"] += 1
                    except: pass
            return dict(sorted(usage.items(), key=lambda x: x[1]['connections'], reverse=True))
        except Exception as e:
            return {"error": str(e)}
    
    # ═══════════════════════════════════════════════════════════════
    # CONNECTIVITY TESTS - Real network calls
    # ═══════════════════════════════════════════════════════════════
    
    def ping(self, host, count=4):
        """Real ping using system command"""
        try:
            param = "-n" if self.is_windows else "-c"
            cmd = ["ping", param, str(count), host]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            
            # Parse ping statistics
            output = result.stdout
            stats = self._parse_ping_stats(output)
            
            self.logs.add(f"Ping {host}: {'OK' if result.returncode == 0 else 'FAIL'}")
            return {
                "success": result.returncode == 0,
                "host": host,
                "output": output,
                "stats": stats
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "host": host, "error": "Timeout"}
        except Exception as e:
            return {"success": False, "host": host, "error": str(e)}
    
    def _parse_ping_stats(self, output):
        """Parse ping output for stats"""
        stats = {"min": None, "max": None, "avg": None, "loss": None}
        try:
            # Windows format
            if "Average" in output:
                m = re.search(r'Average = (\d+)ms', output)
                if m: stats["avg"] = int(m.group(1))
            # Linux format
            elif "min/avg/max" in output:
                m = re.search(r'(\d+\.?\d*)/(\d+\.?\d*)/(\d+\.?\d*)', output)
                if m:
                    stats["min"] = float(m.group(1))
                    stats["avg"] = float(m.group(2))
                    stats["max"] = float(m.group(3))
            # Packet loss
            m = re.search(r'(\d+)%.*loss', output)
            if m: stats["loss"] = int(m.group(1))
        except: pass
        return stats
    
    def traceroute(self, host):
        """Real traceroute"""
        try:
            cmd = ["tracert", "-d", host] if self.is_windows else ["traceroute", "-n", host]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            self.logs.add(f"Traceroute {host}: Complete")
            return {"success": True, "host": host, "output": result.stdout}
        except subprocess.TimeoutExpired:
            return {"success": False, "host": host, "error": "Timeout (>60s)"}
        except Exception as e:
            return {"success": False, "host": host, "error": str(e)}
    
    def check_port(self, host, port, timeout=5):
        """Real TCP port check"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            start = time.time()
            result = sock.connect_ex((host, int(port)))
            elapsed = time.time() - start
            sock.close()
            
            is_open = result == 0
            self.logs.add(f"Port {host}:{port} - {'OPEN' if is_open else 'CLOSED'}")
            return {
                "host": host, "port": port, "open": is_open,
                "response_time": round(elapsed * 1000, 2) if is_open else None
            }
        except socket.timeout:
            return {"host": host, "port": port, "open": False, "error": "Timeout"}
        except Exception as e:
            return {"host": host, "port": port, "error": str(e)}
    
    def port_scan(self, host, ports=None):
        """Scan multiple ports on a host"""
        if ports is None:
            ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 445, 993, 995, 3306, 3389, 5432, 8080, 8443]
        
        results = {"host": host, "open": [], "closed": [], "filtered": []}
        for port in ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                r = sock.connect_ex((host, port))
                sock.close()
                if r == 0:
                    results["open"].append(port)
                else:
                    results["closed"].append(port)
            except:
                results["filtered"].append(port)
        
        self.logs.add(f"Port scan {host}: {len(results['open'])} open")
        return results
    
    def dns_lookup(self, domain):
        """Real DNS lookup"""
        try:
            result = socket.gethostbyname_ex(domain)
            self.logs.add(f"DNS {domain}: {result[2]}")
            return {
                "domain": domain,
                "hostname": result[0],
                "aliases": result[1],
                "ips": result[2]
            }
        except socket.gaierror as e:
            return {"domain": domain, "error": f"DNS resolution failed: {e}"}
        except Exception as e:
            return {"domain": domain, "error": str(e)}
    
    def reverse_dns(self, ip):
        """Reverse DNS lookup"""
        try:
            hostname = socket.gethostbyaddr(ip)
            return {"ip": ip, "hostname": hostname[0], "aliases": hostname[1]}
        except Exception as e:
            return {"ip": ip, "error": str(e)}
    
    def nslookup(self, domain, record_type="A"):
        """Extended DNS lookup using nslookup command"""
        try:
            cmd = ["nslookup", "-type=" + record_type, domain]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return {"domain": domain, "type": record_type, "output": result.stdout}
        except Exception as e:
            return {"error": str(e)}
    
    # ═══════════════════════════════════════════════════════════════
    # NETWORK DISCOVERY
    # ═══════════════════════════════════════════════════════════════
    
    def scan_subnet(self, cidr, timeout=0.5):
        """Scan subnet for active hosts"""
        try:
            network = ipaddress.ip_network(cidr, strict=False)
            if network.num_addresses > 256:
                return {"error": "Subnet too large (max /24)"}
            
            self.logs.add(f"Scanning subnet {cidr}")
            active = []
            
            for ip in network.hosts():
                ip_str = str(ip)
                # Try quick TCP connect on common ports
                for port in [80, 443, 22, 445]:
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(timeout)
                        if sock.connect_ex((ip_str, port)) == 0:
                            active.append({"ip": ip_str, "port": port})
                            sock.close()
                            break
                        sock.close()
                    except: pass
            
            self.logs.add(f"Subnet scan complete: {len(active)} hosts")
            return {"subnet": cidr, "hosts_found": len(active), "hosts": active}
        except Exception as e:
            return {"error": str(e)}
    
    def arp_table(self):
        """Get ARP table"""
        try:
            cmd = ["arp", "-a"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            entries = []
            for line in result.stdout.splitlines():
                # Parse ARP entries
                parts = line.split()
                if len(parts) >= 3:
                    ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                    mac_match = re.search(r'([0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}', line)
                    if ip_match and mac_match:
                        entries.append({"ip": ip_match.group(), "mac": mac_match.group()})
            
            return {"entries": entries, "count": len(entries)}
        except Exception as e:
            return {"error": str(e)}
    
    def get_routing_table(self):
        """Get system routing table"""
        try:
            if self.is_windows:
                cmd = ["route", "print"]
            else:
                cmd = ["ip", "route"] if os.path.exists("/sbin/ip") else ["netstat", "-rn"]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return {"output": result.stdout}
        except Exception as e:
            return {"error": str(e)}
    
    def get_default_gateway(self):
        """Get default gateway"""
        try:
            gateways = []
            if self.is_windows:
                result = subprocess.run(["ipconfig"], capture_output=True, text=True)
                for m in re.finditer(r'Default Gateway.*?:\s*(\d+\.\d+\.\d+\.\d+)', result.stdout):
                    gateways.append(m.group(1))
            else:
                result = subprocess.run(["ip", "route"], capture_output=True, text=True)
                m = re.search(r'default via (\d+\.\d+\.\d+\.\d+)', result.stdout)
                if m: gateways.append(m.group(1))
            return {"gateways": gateways}
        except Exception as e:
            return {"error": str(e)}
    
    # ═══════════════════════════════════════════════════════════════
    # WEB/HTTP OPERATIONS
    # ═══════════════════════════════════════════════════════════════
    
    def check_website(self, url):
        """Check website status"""
        if not REQUESTS_AVAILABLE:
            return {"error": "requests library not installed"}
        
        try:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            start = time.time()
            resp = requests.get(url, timeout=10, allow_redirects=True)
            elapsed = time.time() - start
            
            self.logs.add(f"Website {url}: {resp.status_code}")
            return {
                "url": url,
                "status_code": resp.status_code,
                "status": "UP" if resp.status_code < 400 else "DOWN",
                "response_time": round(elapsed, 3),
                "content_length": len(resp.content),
                "headers": dict(resp.headers)
            }
        except requests.exceptions.SSLError:
            return {"url": url, "status": "SSL_ERROR", "error": "SSL certificate error"}
        except requests.exceptions.ConnectionError:
            return {"url": url, "status": "DOWN", "error": "Connection refused"}
        except requests.exceptions.Timeout:
            return {"url": url, "status": "TIMEOUT", "error": "Request timed out"}
        except Exception as e:
            return {"url": url, "error": str(e)}
    
    def check_ssl_cert(self, host, port=443):
        """Check SSL certificate"""
        try:
            import ssl
            ctx = ssl.create_default_context()
            with ctx.wrap_socket(socket.socket(), server_hostname=host) as s:
                s.settimeout(10)
                s.connect((host, port))
                cert = s.getpeercert()
                
                # Parse expiry
                expiry = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                days_left = (expiry - datetime.now()).days
                
                return {
                    "host": host,
                    "issuer": dict(x[0] for x in cert['issuer']),
                    "subject": dict(x[0] for x in cert['subject']),
                    "expires": cert['notAfter'],
                    "days_until_expiry": days_left,
                    "valid": days_left > 0
                }
        except Exception as e:
            return {"host": host, "error": str(e)}
    
    def http_headers(self, url):
        """Get HTTP headers only"""
        if not REQUESTS_AVAILABLE:
            return {"error": "requests library not installed"}
        try:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            resp = requests.head(url, timeout=10, allow_redirects=True)
            return {"url": url, "status": resp.status_code, "headers": dict(resp.headers)}
        except Exception as e:
            return {"url": url, "error": str(e)}
    
    # ═══════════════════════════════════════════════════════════════
    # SPEED & BANDWIDTH
    # ═══════════════════════════════════════════════════════════════
    
    def speed_test(self):
        """Run internet speed test"""
        if not SPEEDTEST_AVAILABLE:
            return {"error": "speedtest-cli not installed. Run: pip install speedtest-cli"}
        
        try:
            self.logs.add("Speed test started")
            st = speedtest.Speedtest()
            st.get_best_server()
            
            download = st.download() / 1_000_000
            upload = st.upload() / 1_000_000
            ping = st.results.ping
            
            self.logs.add(f"Speed test: {download:.1f} Mbps down, {upload:.1f} Mbps up")
            return {
                "download_mbps": round(download, 2),
                "upload_mbps": round(upload, 2),
                "ping_ms": round(ping, 2),
                "server": st.results.server['name'],
                "server_country": st.results.server['country']
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_bandwidth(self):
        """Calculate current bandwidth usage"""
        try:
            io1 = psutil.net_io_counters()
            time.sleep(1)
            io2 = psutil.net_io_counters()
            
            down = (io2.bytes_recv - io1.bytes_recv) / 1_000_000
            up = (io2.bytes_sent - io1.bytes_sent) / 1_000_000
            
            return {
                "download_mbps": round(down * 8, 2),
                "upload_mbps": round(up * 8, 2),
                "download_MBps": round(down, 2),
                "upload_MBps": round(up, 2)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def measure_latency(self, host="8.8.8.8", count=5):
        """Measure network latency to a host"""
        try:
            total_time = 0
            successful_pings = 0
            
            for i in range(count):
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(2)
                    start = time.time()
                    result = sock.connect_ex((host, 80))
                    elapsed = time.time() - start
                    sock.close()
                    
                    if result == 0:
                        total_time += elapsed
                        successful_pings += 1
                except: pass
            
            if successful_pings > 0:
                avg_latency = total_time / successful_pings
                return {
                    "host": host,
                    "average_latency_ms": round(avg_latency * 1000, 2),
                    "successful_pings": successful_pings,
                    "total_pings": count,
                    "success_rate": round((successful_pings / count) * 100, 2)
                }
            else:
                return {"host": host, "error": "All pings failed"}
        except Exception as e:
            return {"host": host, "error": str(e)}
    
    # ═══════════════════════════════════════════════════════════════
    # SYSTEM HEALTH
    # ═══════════════════════════════════════════════════════════════
    
    def system_health(self):
        """Comprehensive system health check"""
        try:
            cpu = psutil.cpu_percent(interval=1)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            net = self.get_network_stats()
            
            health = {
                "cpu_percent": cpu,
                "cpu_status": "OK" if cpu < 80 else "HIGH" if cpu < 95 else "CRITICAL",
                "memory_percent": mem.percent,
                "memory_used_gb": round(mem.used / (1024**3), 2),
                "memory_total_gb": round(mem.total / (1024**3), 2),
                "memory_status": "OK" if mem.percent < 80 else "HIGH" if mem.percent < 95 else "CRITICAL",
                "disk_percent": disk.percent,
                "disk_used_gb": round(disk.used / (1024**3), 2),
                "disk_total_gb": round(disk.total / (1024**3), 2),
                "disk_status": "OK" if disk.percent < 80 else "HIGH" if disk.percent < 95 else "CRITICAL",
                "network_errors": net.get('errors_in', 0) + net.get('errors_out', 0),
                "network_status": "OK" if (net.get('errors_in', 0) + net.get('errors_out', 0)) < 100 else "WARNING"
            }
            
            # Overall status
            statuses = [health['cpu_status'], health['memory_status'], health['disk_status'], health['network_status']]
            if "CRITICAL" in statuses:
                health['overall'] = "CRITICAL"
            elif "HIGH" in statuses or "WARNING" in statuses:
                health['overall'] = "WARNING"
            else:
                health['overall'] = "HEALTHY"
            
            return health
        except Exception as e:
            return {"error": str(e)}
    
    def check_alerts(self):
        """Check for system alerts"""
        alerts = []
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            cpu = psutil.cpu_percent(interval=0.5)
            if cpu > 85:
                alerts.append({"time": ts, "severity": "CRITICAL" if cpu > 95 else "HIGH", "type": "CPU", "msg": f"High CPU: {cpu}%"})
            
            mem = psutil.virtual_memory()
            if mem.percent > 85:
                alerts.append({"time": ts, "severity": "CRITICAL" if mem.percent > 95 else "HIGH", "type": "Memory", "msg": f"High memory: {mem.percent}%"})
            
            disk = psutil.disk_usage('/')
            if disk.percent > 85:
                alerts.append({"time": ts, "severity": "CRITICAL" if disk.percent > 95 else "HIGH", "type": "Disk", "msg": f"High disk: {disk.percent}%"})
            
            io = psutil.net_io_counters()
            if io.errin > 100 or io.errout > 100:
                alerts.append({"time": ts, "severity": "MEDIUM", "type": "Network", "msg": f"Network errors: IN({io.errin}) OUT({io.errout})"})
        except: pass
        
        for a in alerts:
            self.alerts.append(a)
        
        return alerts
    
    def get_recent_alerts(self, hours=24):
        """Get recent alerts"""
        cutoff = datetime.now() - timedelta(hours=hours)
        result = []
        for a in self.alerts:
            try:
                if datetime.strptime(a['time'], "%Y-%m-%d %H:%M:%S") > cutoff:
                    result.append(a)
            except: pass
        return result
    
    def summarize_logs(self, hours=24, use_ml=True):
        """Generate summary of recent logs"""
        return self.logs.summarize_logs(hours, use_ml)


# ═══════════════════════════════════════════════════════════════════════
# CHATBOT ENGINE
# ═══════════════════════════════════════════════════════════════════════

class NetworkChatbot:
    """ChatOps interface for network operations with enhanced log summarization"""
    
    def __init__(self):
        self.ops = NetworkOperations()
        self.commands = self._build_command_map()
    
    def _build_command_map(self):
        """Map keywords to handlers"""
        return {
            # Greetings
            "greeting": (["hi", "hello", "hey", "greetings", "howdy", "yo", "sup"], self._greet),
            "thanks": (["thanks", "thank", "thx", "ty", "appreciate"], self._thanks),
            "bye": (["bye", "goodbye", "cya", "farewell", "later"], self._bye),
            
            # Network Status
            "status": (["network status", "netstat", "network overview", "show status"], self._network_status),
            "interfaces": (["interface", "adapter", "network card", "nic", "show interfaces"], self._interfaces),
            "connections": (["connection", "established", "who connected", "show connections"], self._connections),
            "listening": (["listening", "open ports", "ports listening", "listening ports"], self._listening_ports),
            "process_net": (["process network", "which process", "app network", "process network usage"], self._process_network),
            
            # Connectivity
            "ping": (["ping"], self._ping),
            "traceroute": (["traceroute", "tracert", "trace route", "trace path"], self._traceroute),
            "port_check": (["check port", "port open", "test port"], self._port_check),
            "port_scan": (["port scan", "scan ports"], self._port_scan),
            
            # DNS
            "dns": (["dns lookup", "resolve", "nslookup"], self._dns),
            "reverse_dns": (["reverse dns", "ptr", "ip to hostname"], self._reverse_dns),
            
            # Discovery
            "subnet_scan": (["scan subnet", "discover host", "find device", "network scan"], self._subnet_scan),
            "arp": (["arp", "mac address", "arp table"], self._arp),
            "routing": (["routing", "route table", "routes", "routing table"], self._routing),
            "gateway": (["gateway", "default gateway"], self._gateway),
            
            # Web/HTTP
            "website": (["website status", "check site", "is site up", "http check", "check website"], self._website),
            "ssl": (["ssl", "certificate", "cert check", "https", "check ssl"], self._ssl),
            "headers": (["http header", "response header", "http headers"], self._headers),
            
            # Speed & Bandwidth
            "speed": (["speed test", "test speed", "internet speed", "speedtest"], self._speed_test),
            "bandwidth": (["bandwidth", "throughput", "network usage"], self._bandwidth),
            "latency": (["latency", "measure latency", "network latency"], self._latency),
            
            # Health & Alerts
            "health": (["health", "system check", "system status", "system health"], self._health),
            "alerts": (["alert", "warning", "critical", "show alerts"], self._alerts),
            
            # Diagnostics
            "diagnose": (["diagnose", "troubleshoot", "latency", "slow network", "lag", "diagnose network"], self._diagnose),
            
            # Logs
            "logs": (["log", "summarize", "history", "show logs"], self._logs),
            "summarize_logs": (["summarize logs", "log summary", "logs summary", "ai summary", "smart summary"], self._summarize_logs),
            "analyze_logs": (["analyze logs", "log analysis", "ml summary"], self._analyze_logs),
            
            # Help
            "help": (["help", "command", "what can you", "how to"], self._help),
        }
    
    def process(self, message):
        """Process user message"""
        msg = message.lower().strip()
        
        # Find matching command
        for cmd_name, (keywords, handler) in self.commands.items():
            for kw in keywords:
                if kw in msg or msg == kw:
                    return handler(message)
        
        return self._unknown()
    
    # ═══════════════════════════════════════════════════════════════
    # HANDLER METHODS
    # ═══════════════════════════════════════════════════════════════
    
    def _greet(self, msg):
        responses = [
            "Hello! I'm NexoOps, your Network ChatOps assistant. How can I help?",
            "Hi there! Ready to assist with network operations. What do you need?",
            "Hey! I'm here to help with network diagnostics, monitoring, and more!",
            "Greetings! Ask me about network status, ping hosts, scan ports, and more!"
        ]
        return f"[ICON:wave] {random.choice(responses)}"
    
    def _thanks(self, msg):
        responses = ["You're welcome!", "Happy to help!", "Anytime!", "Glad I could assist!"]
        return f"[ICON:smile] {random.choice(responses)}"
    
    def _bye(self, msg):
        responses = ["Goodbye! Stay connected!", "See you later!", "Farewell! Your network is in good hands!"]
        return f"[ICON:wave] {random.choice(responses)}"
    
    def _unknown(self):
        return "[ICON:help-circle] I didn't understand that. Type 'help' to see available commands.\n\nTry: 'network status', 'ping 8.8.8.8', 'check port 80', 'speed test', etc."
    
    def _network_status(self, msg):
        stats = self.ops.get_network_stats()
        if "error" in stats:
            return f"[ICON:x-circle] Error: {stats['error']}"
        
        r = "[ICON:activity] NETWORK STATUS\n"
        r += "━" * 40 + "\n"
        r += f"[ICON:link] Established Connections: {stats['established']}\n"
        r += f"[ICON:server] Listening Ports: {stats['listening']}\n"
        r += f"[ICON:globe] Total Connections: {stats['total_connections']}\n"
        r += f"\n[ICON:upload] Data Sent: {stats['bytes_sent'] // (1024*1024)} MB\n"
        r += f"[ICON:download] Data Received: {stats['bytes_recv'] // (1024*1024)} MB\n"
        r += f"[ICON:package] Packets Sent: {stats['packets_sent']:,}\n"
        r += f"[ICON:package] Packets Received: {stats['packets_recv']:,}\n"
        
        if stats['errors_in'] > 0 or stats['errors_out'] > 0:
            r += f"\n[ICON:alert-triangle] Errors: IN({stats['errors_in']}) OUT({stats['errors_out']})\n"
        if stats['drops_in'] > 0 or stats['drops_out'] > 0:
            r += f"[ICON:alert-triangle] Drops: IN({stats['drops_in']}) OUT({stats['drops_out']})\n"
        
        return r
    
    def _interfaces(self, msg):
        ifaces = self.ops.get_interfaces()
        if isinstance(ifaces, dict) and "error" in ifaces:
            return f"[ICON:x-circle] Error: {ifaces['error']}"
        
        r = f"[ICON:wifi] NETWORK INTERFACES ({len(ifaces)} found)\n"
        r += "━" * 40 + "\n"
        
        for iface in ifaces:
            icon = "[ICON:check-circle]" if iface['is_up'] else "[ICON:x-circle]"
            r += f"\n{icon} {iface['name']}\n"
            r += f"   Status: {'UP' if iface['is_up'] else 'DOWN'}"
            if iface['speed'] > 0:
                r += f" | Speed: {iface['speed']} Mbps"
            if iface['mtu'] > 0:
                r += f" | MTU: {iface['mtu']}"
            r += "\n"
            
            for addr in iface['addresses']:
                if addr['family'] in ['AF_INET', 'AF_INET6']:
                    r += f"   {addr['family']}: {addr['address']}\n"
        
        return r
    
    def _connections(self, msg):
        conns = self.ops.get_connections(limit=20)
        if isinstance(conns, dict) and "error" in conns:
            return f"[ICON:x-circle] Error: {conns['error']}"
        
        r = f"[ICON:link] ACTIVE CONNECTIONS ({len(conns)} shown)\n"
        r += "━" * 40 + "\n"
        
        for c in conns[:15]:
            r += f"[ICON:arrow-right] {c['local']} → {c['remote']}\n"
            r += f"   Process: {c['process']} (PID: {c['pid']})\n"
        
        if len(conns) > 15:
            r += f"\n... and {len(conns) - 15} more\n"
        
        return r
    
    def _listening_ports(self, msg):
        ports = self.ops.get_listening_ports()
        if isinstance(ports, dict) and "error" in ports:
            return f"[ICON:x-circle] Error: {ports['error']}"
        
        r = f"[ICON:server] LISTENING PORTS ({len(ports)} found)\n"
        r += "━" * 40 + "\n"
        
        for p in ports[:20]:
            r += f"[ICON:radio] {p['address']}:{p['port']} - {p['process']}\n"
        
        if len(ports) > 20:
            r += f"\n... and {len(ports) - 20} more\n"
        
        return r
    
    def _process_network(self, msg):
        usage = self.ops.get_process_network_usage()
        if isinstance(usage, dict) and "error" in usage:
            return f"[ICON:x-circle] Error: {usage['error']}"
        
        r = "[ICON:cpu] NETWORK USAGE BY PROCESS\n"
        r += "━" * 40 + "\n"
        
        for name, info in list(usage.items())[:15]:
            r += f"[ICON:terminal] {name}\n"
            r += f"   Connections: {info['connections']} (Est: {info['established']}, Listen: {info['listening']})\n"
        
        return r
    
    def _ping(self, msg):
        # Extract target
        target = self._extract_host(msg)
        if not target:
            return "[ICON:help-circle] Please specify a host.\nExample: 'ping 8.8.8.8' or 'ping google.com'"
        
        result = self.ops.ping(target)
        
        if result['success']:
            r = f"[ICON:check-circle] PING {target} - SUCCESS\n"
            r += "━" * 40 + "\n"
            if result['stats']['avg']:
                r += f"Average: {result['stats']['avg']} ms\n"
            if result['stats']['loss'] is not None:
                r += f"Packet Loss: {result['stats']['loss']}%\n"
            r += f"\n{result['output']}"
        else:
            r = f"[ICON:x-circle] PING {target} - FAILED\n"
            r += f"Error: {result.get('error', 'Host unreachable')}"
        
        return r
    
    def _traceroute(self, msg):
        target = self._extract_host(msg)
        if not target:
            return "[ICON:help-circle] Please specify a host.\nExample: 'traceroute google.com'"
        
        r = f"[ICON:loader] Running traceroute to {target}...\n\n"
        result = self.ops.traceroute(target)
        
        if result['success']:
            return f"[ICON:map] TRACEROUTE TO {target}\n{'━' * 40}\n{result['output']}"
        else:
            return f"[ICON:x-circle] Traceroute failed: {result.get('error', 'Unknown error')}"
    
    def _port_check(self, msg):
        host = self._extract_ip(msg) or self._extract_domain(msg)
        port = self._extract_port(msg)
        
        if not host or not port:
            return "[ICON:help-circle] Please specify host and port.\nExample: 'check port 192.168.1.1:80' or 'test port 443 on google.com'"
        
        result = self.ops.check_port(host, port)
        
        if "error" in result:
            return f"[ICON:x-circle] Error: {result['error']}"
        
        if result['open']:
            r = f"[ICON:unlock] PORT {port} on {host} is OPEN\n"
            if result.get('response_time'):
                r += f"Response time: {result['response_time']} ms"
        else:
            r = f"[ICON:lock] PORT {port} on {host} is CLOSED"
        
        return r
    
    def _port_scan(self, msg):
        host = self._extract_ip(msg) or self._extract_domain(msg)
        if not host:
            return "[ICON:help-circle] Please specify a host.\nExample: 'port scan 192.168.1.1'"
        
        result = self.ops.port_scan(host)
        
        if "error" in result:
            return f"[ICON:x-circle] Error: {result['error']}"
        
        r = f"[ICON:search] PORT SCAN: {host}\n"
        r += "━" * 40 + "\n"
        r += f"[ICON:unlock] Open: {result['open'] if result['open'] else 'None'}\n"
        r += f"[ICON:lock] Closed: {len(result['closed'])} ports\n"
        
        return r
    
    def _dns(self, msg):
        domain = self._extract_domain(msg)
        if not domain:
            return "[ICON:help-circle] Please specify a domain.\nExample: 'dns lookup google.com'"
        
        result = self.ops.dns_lookup(domain)
        
        if "error" in result:
            return f"[ICON:x-circle] DNS lookup failed: {result['error']}"
        
        r = f"[ICON:globe] DNS LOOKUP: {domain}\n"
        r += "━" * 40 + "\n"
        r += f"Hostname: {result['hostname']}\n"
        r += f"IP Addresses: {', '.join(result['ips'])}\n"
        if result['aliases']:
            r += f"Aliases: {', '.join(result['aliases'])}\n"
        
        return r
    
    def _reverse_dns(self, msg):
        ip = self._extract_ip(msg)
        if not ip:
            return "[ICON:help-circle] Please specify an IP.\nExample: 'reverse dns 8.8.8.8'"
        
        result = self.ops.reverse_dns(ip)
        
        if "error" in result:
            return f"[ICON:x-circle] Reverse DNS failed: {result['error']}"
        
        return f"[ICON:globe] REVERSE DNS: {ip}\n{'━' * 40}\nHostname: {result['hostname']}"
    
    def _subnet_scan(self, msg):
        subnet = self._extract_subnet(msg)
        if not subnet:
            return "[ICON:help-circle] Please specify a subnet.\nExample: 'scan subnet 192.168.1.0/24'"
        
        r = f"[ICON:loader] Scanning {subnet}...\n"
        result = self.ops.scan_subnet(subnet)
        
        if "error" in result:
            return f"[ICON:x-circle] Error: {result['error']}"
        
        r = f"[ICON:search] SUBNET SCAN: {subnet}\n"
        r += "━" * 40 + "\n"
        r += f"Hosts found: {result['hosts_found']}\n\n"
        
        for h in result['hosts'][:20]:
            r += f"[ICON:server] {h['ip']} (port {h['port']} open)\n"
        
        if result['hosts_found'] > 20:
            r += f"\n... and {result['hosts_found'] - 20} more\n"
        
        return r
    
    def _arp(self, msg):
        result = self.ops.arp_table()
        
        if "error" in result:
            return f"[ICON:x-circle] Error: {result['error']}"
        
        r = f"[ICON:list] ARP TABLE ({result['count']} entries)\n"
        r += "━" * 40 + "\n"
        
        for e in result['entries'][:20]:
            r += f"{e['ip']} → {e['mac']}\n"
        
        return r
    
    def _routing(self, msg):
        result = self.ops.get_routing_table()
        
        if "error" in result:
            return f"[ICON:x-circle] Error: {result['error']}"
        
        return f"[ICON:map] ROUTING TABLE\n{'━' * 40}\n{result['output']}"
    
    def _gateway(self, msg):
        result = self.ops.get_default_gateway()
        
        if "error" in result:
            return f"[ICON:x-circle] Error: {result['error']}"
        
        gws = result.get('gateways', [])
        if gws:
            return f"[ICON:home] Default Gateway: {', '.join(gws)}"
        else:
            return "[ICON:alert-circle] No default gateway found"
    
    def _website(self, msg):
        url = self._extract_domain(msg) or self._extract_url(msg)
        if not url:
            return "[ICON:help-circle] Please specify a URL.\nExample: 'check website google.com'"
        
        result = self.ops.check_website(url)
        
        if "error" in result:
            return f"[ICON:x-circle] Error: {result['error']}"
        
        icon = "[ICON:check-circle]" if result['status'] == "UP" else "[ICON:x-circle]"
        r = f"{icon} WEBSITE STATUS: {result['url']}\n"
        r += "━" * 40 + "\n"
        r += f"Status: {result['status']} (HTTP {result['status_code']})\n"
        r += f"Response Time: {result['response_time']} seconds\n"
        r += f"Content Size: {result['content_length']} bytes\n"
        
        return r
    
    def _ssl(self, msg):
        host = self._extract_domain(msg)
        if not host:
            return "[ICON:help-circle] Please specify a domain.\nExample: 'check ssl google.com'"
        
        result = self.ops.check_ssl_cert(host)
        
        if "error" in result:
            return f"[ICON:x-circle] SSL check failed: {result['error']}"
        
        icon = "[ICON:check-circle]" if result['valid'] else "[ICON:alert-triangle]"
        r = f"{icon} SSL CERTIFICATE: {host}\n"
        r += "━" * 40 + "\n"
        r += f"Issuer: {result['issuer'].get('organizationName', 'N/A')}\n"
        r += f"Subject: {result['subject'].get('commonName', 'N/A')}\n"
        r += f"Expires: {result['expires']}\n"
        r += f"Days Until Expiry: {result['days_until_expiry']}\n"
        r += f"Valid: {'Yes' if result['valid'] else 'NO - EXPIRED!'}\n"
        
        return r
    
    def _headers(self, msg):
        url = self._extract_domain(msg)
        if not url:
            return "[ICON:help-circle] Please specify a URL.\nExample: 'http headers google.com'"
        
        result = self.ops.http_headers(url)
        
        if "error" in result:
            return f"[ICON:x-circle] Error: {result['error']}"
        
        r = f"[ICON:file-text] HTTP HEADERS: {result['url']}\n"
        r += "━" * 40 + "\n"
        
        for k, v in list(result['headers'].items())[:15]:
            r += f"{k}: {v[:50]}{'...' if len(str(v)) > 50 else ''}\n"
        
        return r
    
    def _speed_test(self, msg):
        r = "[ICON:loader] Running speed test... This may take 30-60 seconds.\n"
        result = self.ops.speed_test()
        
        if "error" in result:
            return f"[ICON:x-circle] Speed test failed: {result['error']}"
        
        r = "[ICON:zap] SPEED TEST RESULTS\n"
        r += "━" * 40 + "\n"
        r += f"[ICON:download] Download: {result['download_mbps']} Mbps\n"
        r += f"[ICON:upload] Upload: {result['upload_mbps']} Mbps\n"
        r += f"[ICON:activity] Ping: {result['ping_ms']} ms\n"
        r += f"[ICON:server] Server: {result['server']} ({result['server_country']})\n"
        
        return r
    
    def _bandwidth(self, msg):
        result = self.ops.get_bandwidth()
        
        if "error" in result:
            return f"[ICON:x-circle] Error: {result['error']}"
        
        r = "[ICON:trending-up] CURRENT BANDWIDTH USAGE\n"
        r += "━" * 40 + "\n"
        r += f"[ICON:download] Download: {result['download_mbps']} Mbps ({result['download_MBps']} MB/s)\n"
        r += f"[ICON:upload] Upload: {result['upload_mbps']} Mbps ({result['upload_MBps']} MB/s)\n"
        
        return r
    
    def _latency(self, msg):
        host = self._extract_host(msg) or "8.8.8.8"
        result = self.ops.measure_latency(host)
        
        if "error" in result:
            return f"[ICON:x-circle] Error measuring latency: {result['error']}"
        
        r = f"[ICON:clock] NETWORK LATENCY: {host}\n"
        r += "━" * 40 + "\n"
        r += f"Average Latency: {result['average_latency_ms']} ms\n"
        r += f"Success Rate: {result['success_rate']}% ({result['successful_pings']}/{result['total_pings']})\n"
        
        # Interpretation
        latency = result['average_latency_ms']
        if latency < 50:
            r += "Quality: Excellent (Gaming/VoIP ready)\n"
        elif latency < 100:
            r += "Quality: Good (Streaming/Web browsing)\n"
        elif latency < 200:
            r += "Quality: Fair (Basic web usage)\n"
        else:
            r += "Quality: Poor (High latency detected)\n"
        
        return r
    
    def _health(self, msg):
        result = self.ops.system_health()
        
        if "error" in result:
            return f"[ICON:x-circle] Error: {result['error']}"
        
        def icon(status):
            return {"OK": "[ICON:check-circle]", "HIGH": "[ICON:alert-triangle]", "CRITICAL": "[ICON:x-circle]", "WARNING": "[ICON:alert-triangle]"}.get(status, "[ICON:info]")
        
        r = f"[ICON:heart] SYSTEM HEALTH: {result['overall']}\n"
        r += "━" * 40 + "\n"
        r += f"{icon(result['cpu_status'])} CPU: {result['cpu_percent']}%\n"
        r += f"{icon(result['memory_status'])} Memory: {result['memory_percent']}% ({result['memory_used_gb']}/{result['memory_total_gb']} GB)\n"
        r += f"{icon(result['disk_status'])} Disk: {result['disk_percent']}% ({result['disk_used_gb']}/{result['disk_total_gb']} GB)\n"
        r += f"{icon(result['network_status'])} Network Errors: {result['network_errors']}\n"
        
        return r
    
    def _alerts(self, msg):
        # Check current alerts
        current = self.ops.check_alerts()
        recent = self.ops.get_recent_alerts(hours=24)
        
        if not current and not recent:
            return "[ICON:check-circle] No alerts. System is healthy!"
        
        r = f"[ICON:alert-triangle] SYSTEM ALERTS\n"
        r += "━" * 40 + "\n"
        
        all_alerts = current + recent
        for a in all_alerts[-10:]:
            sev_icon = {"CRITICAL": "[ICON:x-circle]", "HIGH": "[ICON:alert-triangle]", "MEDIUM": "[ICON:alert-circle]"}.get(a['severity'], "[ICON:info]")
            r += f"{sev_icon} [{a['severity']}] {a['type']}: {a['msg']}\n"
        
        return r
    
    def _diagnose(self, msg):
        r = "[ICON:stethoscope] NETWORK DIAGNOSTICS\n"
        r += "━" * 40 + "\n"
        
        # Gateway check
        gw = self.ops.get_default_gateway()
        if gw.get('gateways'):
            gateway = gw['gateways'][0]
            gw_ping = self.ops.ping(gateway, count=2)
            if gw_ping['success']:
                r += f"[ICON:check-circle] Gateway ({gateway}): Reachable\n"
            else:
                r += f"[ICON:x-circle] Gateway ({gateway}): UNREACHABLE\n"
        
        # Internet check
        dns_ping = self.ops.ping("8.8.8.8", count=2)
        if dns_ping['success']:
            r += "[ICON:check-circle] Internet (8.8.8.8): Connected\n"
        else:
            r += "[ICON:x-circle] Internet (8.8.8.8): NO CONNECTION\n"
        
        # DNS check
        dns = self.ops.dns_lookup("google.com")
        if "error" not in dns:
            r += "[ICON:check-circle] DNS Resolution: Working\n"
        else:
            r += "[ICON:x-circle] DNS Resolution: FAILED\n"
        
        # Bandwidth
        bw = self.ops.get_bandwidth()
        if "error" not in bw:
            r += f"\n[ICON:trending-up] Current Bandwidth:\n"
            r += f"   Download: {bw['download_mbps']} Mbps\n"
            r += f"   Upload: {bw['upload_mbps']} Mbps\n"
        
        # Network errors
        stats = self.ops.get_network_stats()
        if "error" not in stats:
            errors = stats['errors_in'] + stats['errors_out']
            drops = stats['drops_in'] + stats['drops_out']
            if errors > 0 or drops > 0:
                r += f"\n[ICON:alert-triangle] Issues detected:\n"
                if errors > 0:
                    r += f"   Network errors: {errors}\n"
                if drops > 0:
                    r += f"   Packet drops: {drops}\n"
        
        return r
    
    def _logs(self, msg):
        hours = self._extract_hours(msg) or 1
        logs = self.ops.logs.get_text(hours=hours)
        
        if not logs:
            return f"[ICON:file-text] No logs in the last {hours} hour(s)."
        
        lines = logs.split('\n')
        r = f"[ICON:file-text] LOGS (Last {hours} hour(s))\n"
        r += "━" * 40 + "\n"
        r += f"Total entries: {len(lines)}\n\n"
        
        # Show last 20 entries
        for line in lines[-20:]:
            r += f"{line}\n"
        
        return r
    
    def _summarize_logs(self, msg):
        """Smart log summarization using ML"""
        hours = self._extract_hours(msg) or 24
        use_ml = "basic" not in msg.lower()
        
        r = f"[ICON:brain] ANALYZING LOGS (Last {hours} hours)...\n\n"
        summary = self.ops.summarize_logs(hours, use_ml=use_ml)
        
        return summary
    
    def _analyze_logs(self, msg):
        """Force ML-based log analysis"""
        hours = self._extract_hours(msg) or 24
        
        if not ML_AVAILABLE:
            r = "[ICON:alert-triangle] AI ANALYSIS UNAVAILABLE\n"
            r += "━" * 40 + "\n"
            r += "To enable smart log analysis, install:\n"
            r += "• pip install scikit-learn nltk\n\n"
            r += "Using basic summary instead:\n\n"
            r += self.ops.summarize_logs(hours, use_ml=False)
            return r
        
        r = f"[ICON:brain] AI-POWERED LOG ANALYSIS (Last {hours} hours)\n"
        r += "━" * 40 + "\n\n"
        r += self.ops.summarize_logs(hours, use_ml=True)
        
        return r
    
    def _help(self, msg):
        help_text = """[ICON:help-circle] NEXOOPS NETWORK CHATOPS - COMMANDS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[ICON:activity] NETWORK STATUS
• network status - Overview of network stats
• show interfaces - List network adapters
• show connections - Active connections
• listening ports - Open/listening ports
• process network usage - Network by process

[ICON:wifi] CONNECTIVITY TESTS
• ping <host> - Ping a host (ping 8.8.8.8)
• traceroute <host> - Trace route to host
• check port <host>:<port> - Test if port is open
• port scan <host> - Scan common ports

[ICON:globe] DNS OPERATIONS
• dns lookup <domain> - Resolve domain to IP
• reverse dns <ip> - Get hostname from IP
• nslookup <domain> - Extended DNS query

[ICON:search] NETWORK DISCOVERY
• scan subnet <cidr> - Find hosts (192.168.1.0/24)
• arp table - Show ARP entries
• routing table - Show routes
• default gateway - Show gateway

[ICON:link] WEB/HTTP CHECKS
• check website <url> - Test if site is up
• check ssl <domain> - Verify SSL certificate
• http headers <url> - Get response headers

[ICON:zap] SPEED & BANDWIDTH
• speed test - Run internet speed test
• bandwidth - Current bandwidth usage
• latency - Measure network latency

[ICON:heart] SYSTEM HEALTH
• system health - CPU, memory, disk, network
• show alerts - View system alerts
• diagnose network - Full network diagnosis

[ICON:brain] SMART LOG ANALYSIS
• summarize logs - AI-powered log summary
• analyze logs - ML-based log analysis
• show logs - Raw log view
• logs last 2 hours - Time-filtered logs

[ICON:zap] EXAMPLES
• ping google.com
• summarize logs last 24 hours
• analyze logs
• check port 192.168.1.1:22
• scan subnet 192.168.1.0/24
"""
        return help_text
    
    # ═══════════════════════════════════════════════════════════════
    # EXTRACTION HELPERS
    # ═══════════════════════════════════════════════════════════════
    
    def _extract_ip(self, msg):
        m = re.search(r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b', msg)
        return m.group(1) if m else None
    
    def _extract_domain(self, msg):
        m = re.search(r'\b([a-zA-Z0-9][-a-zA-Z0-9]*\.[a-zA-Z]{2,}(?:\.[a-zA-Z]{2,})?)\b', msg)
        return m.group(1) if m else None
    
    def _extract_url(self, msg):
        m = re.search(r'(https?://[^\s]+)', msg)
        return m.group(1) if m else None
    
    def _extract_port(self, msg):
        # Try :port format
        m = re.search(r':(\d+)', msg)
        if m: return int(m.group(1))
        # Try "port X" format
        m = re.search(r'port\s+(\d+)', msg.lower())
        if m: return int(m.group(1))
        return None
    
    def _extract_subnet(self, msg):
        m = re.search(r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2})\b', msg)
        return m.group(1) if m else None
    
    def _extract_host(self, msg):
        # Try IP first
        ip = self._extract_ip(msg)
        if ip: return ip
        # Try domain
        domain = self._extract_domain(msg)
        if domain: return domain
        # Try extracting word after command
        words = msg.split()
        for i, w in enumerate(words):
            if w.lower() in ['ping', 'traceroute', 'tracert', 'to']:
                if i + 1 < len(words):
                    return words[i + 1]
        return None
    
    def _extract_hours(self, msg):
        m = re.search(r'(\d+)\s*hour', msg.lower())
        if m: return int(m.group(1))
        if 'last hour' in msg.lower(): return 1
        return None


# ═══════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINTS
# ═══════════════════════════════════════════════════════════════════════

_bot = None

def get_chatbot():
    global _bot
    if _bot is None:
        _bot = NetworkChatbot()
    return _bot

def chatbot_response(message, log_context=""):
    return get_chatbot().process(message)

def set_uploaded_logs(text):
    get_chatbot().ops.logs.set_uploaded(text)


if __name__ == "__main__":
    bot = NetworkChatbot()
    
    print("\n" + "=" * 60)
    print("NEXOOPS NETWORK CHATOPS - ENHANCED WITH AI SUMMARIZATION")
    print("=" * 60)
    
    tests = [
        "hello",
        "summarize logs",
        "analyze logs last 2 hours",
        "show logs",
        "network status",
        "help"
    ]
    
    for t in tests:
        print(f"\n>>> {t}")
        print("-" * 40)
        resp = bot.process(t)
        print(resp)