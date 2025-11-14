# ================================================
# ENHANCED ALERT CLASSIFICATION SYSTEM FOR PLAIN LOGS
# ================================================
from summarizer import summarize_log
import re
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# -----------------------------
# STEP 1: CLEAN LOG TEXT
# -----------------------------
def clean_text(text):
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', ' IPADDR ', text)
    text = re.sub(r'\[.*?\]', ' ', text)
    text = re.sub(r'\{.*?\}', ' ', text)
    text = re.sub(r'\(.*?\)', ' ', text)
    text = re.sub(r'\b(0x)?[0-9a-f]+\b', ' HEX ', text)
    text = re.sub(r'\b\d+\b', ' NUM ', text)
    text = re.sub(r'[^a-z\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# -----------------------------
# STEP 2: FEATURE EXTRACTION
# -----------------------------
def extract_features(text):
    features = {}
    features['char_count'] = len(text)
    features['word_count'] = len(text.split())
    critical_keywords = ['error', 'failed', 'critical', 'fatal', 'panic', 'crash', 'corruption', 'breach']
    warning_keywords = ['warning', 'timeout', 'slow', 'high', 'full', 'exceeded', 'congestion']
    info_keywords = ['success', 'completed', 'started', 'normal', 'stable']
    features['critical_words'] = sum(1 for word in critical_keywords if word in text)
    features['warning_words'] = sum(1 for word in warning_keywords if word in text)
    features['info_words'] = sum(1 for word in info_keywords if word in text)
    return features

# -----------------------------
# STEP 3: GENERATE SYNTHETIC LOG DATA FOR TRAINING
# -----------------------------
def generate_enterprise_logs(n_samples=5000):
    np.random.seed(42)
    templates = {
        'Low': ["system rebooted successfully at TIMESTAMP", "service SERVICE started normally", "configuration file CONFIG loaded successfully"],
        'Medium': ["minor delay detected in response time for SERVICE", "network latency slightly above normal on INTERFACE"],
        'High': ["disk usage at NUM percent warning issued", "connection timeout detected multiple times for SERVICE"],
        'Critical': ["authentication failed for user root from IPADDR", "database connection lost during backup operation"]
    }

    severity_weights = [0.4, 0.3, 0.2, 0.1]
    data = []
    for _ in range(n_samples):
        severity = np.random.choice(['Low','Medium','High','Critical'], p=severity_weights)
        template = np.random.choice(templates[severity])
        log_entry = template.replace('TIMESTAMP', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        log_entry = log_entry.replace('SERVICE', np.random.choice(['ssh','httpd','mysql','nginx','redis']))
        log_entry = log_entry.replace('IPADDR', f"{np.random.randint(1,255)}.{np.random.randint(1,255)}.{np.random.randint(1,255)}.{np.random.randint(1,255)}")
        log_entry = log_entry.replace('CONFIG', np.random.choice(['/etc/app.conf','config.yaml','settings.json']))
        log_entry = log_entry.replace('INTERFACE', np.random.choice(['eth0','eth1','bond0','wlan0']))
        log_entry = log_entry.replace('NUM', str(np.random.randint(1,100)))
        data.append((log_entry, severity))
    return pd.DataFrame(data, columns=["summary","severity"])

def load_training_data():
    df = generate_enterprise_logs(5000)
    df['cleaned_text'] = df['summary'].apply(clean_text)
    feature_data = df['summary'].apply(extract_features).apply(pd.Series)
    df = pd.concat([df, feature_data], axis=1)
    return df

# -----------------------------
# STEP 4: TRAIN MODEL
# -----------------------------
def train_alert_model():
    df = load_training_data()
    X_text = df['cleaned_text']
    feature_columns = ['char_count','word_count','critical_words','warning_words','info_words']
    X_features = df[feature_columns]
    y = df['severity']

    X_train_text, X_test_text, y_train, y_test = train_test_split(
        X_text, y, test_size=0.2, random_state=42, stratify=y
    )
    X_train_features = X_features.loc[X_train_text.index]
    X_test_features = X_features.loc[X_test_text.index]

    preprocessor = ColumnTransformer([
        ('tfidf', TfidfVectorizer(max_features=5000, ngram_range=(1,3), min_df=2, max_df=0.8, sublinear_tf=True), 'text'),
        ('num', StandardScaler(), feature_columns)
    ], remainder='drop')

    X_train_combined = pd.concat([X_train_text.rename('text'), X_train_features], axis=1)
    X_test_combined = pd.concat([X_test_text.rename('text'), X_test_features], axis=1)

    models = {
        'random_forest': RandomForestClassifier(n_estimators=200, random_state=42),
        'svm': SVC(probability=True, random_state=42),
        'logistic_regression': LogisticRegression(max_iter=1000, random_state=42)
    }

    pipelines = {}
    best_model = None
    best_score = 0

    for name, model in models.items():
        pipe = Pipeline([('preprocessor', preprocessor), ('clf', model)])
        pipe.fit(X_train_combined, y_train)
        y_pred = pipe.predict(X_test_combined)
        acc = accuracy_score(y_test, y_pred)
        if acc > best_score:
            best_score = acc
            best_model = name
            best_pipeline = pipe

    joblib.dump(best_pipeline, "alert_model.joblib")
    print(f"🏆 Best model: {best_model} with accuracy {best_score:.4f}")
    return best_pipeline

# -----------------------------
# STEP 5: PREDICT SEVERITY FOR SINGLE LOG
# -----------------------------
def predict_severity_from_log(log_text):
    try:
        model = joblib.load("alert_model.joblib")
    except FileNotFoundError:
        print("❌ Model not found. Train the model first.")
        return None, None

    summary = summarize_log(log_text, n_sentences=2, num_clusters=2)
    if not summary.strip():
        summary = log_text
    clean_summary = clean_text(summary)

    feature_data = extract_features(clean_summary)
    feature_data['text'] = clean_summary
    X_df = pd.DataFrame([feature_data])

    for col in ['char_count','word_count','critical_words','warning_words','info_words']:
        if col not in X_df.columns:
            X_df[col] = 0

    prediction = model.predict(X_df)[0]

    try:
        probabilities = model.predict_proba(X_df)[0]
        labels = model.classes_
        prob_dict = {labels[i]: round(probabilities[i]*100,2) for i in range(len(labels))}
    except:
        prob_dict = None

    return prediction, prob_dict

# -----------------------------
# STEP 6: PREDICT BATCH LOGS
# -----------------------------
def predict_batch_logs_plain_txt(log_files):
    results = []
    for log_file in log_files:
        print(f"\nProcessing: {log_file}")
        try:
            with open(log_file,'r',encoding='utf-8') as f:
                lines = f.readlines()
            for line_num, log_text in enumerate(lines,1):
                log_text = log_text.strip()
                if not log_text:
                    continue
                severity, probabilities = predict_severity_from_log(log_text)
                results.append({
                    'file': log_file,
                    'line': line_num,
                    'severity': severity,
                    'probabilities': probabilities
                })
        except Exception as e:
            print(f"❌ Error reading {log_file}: {str(e)}")
            results.append({'file': log_file,'line':None,'severity':'Error','probabilities':None})
    return results

def classify_log(text):
    severity, probabilities = predict_severity_from_log(text)
    return {
        "severity": severity,
        "probabilities": probabilities
    }


# -----------------------------
# MAIN EXECUTION
# -----------------------------
if __name__ == "__main__":
    print("🚀 ALERT CLASSIFICATION SYSTEM FOR PLAIN LOGS")
    print("="*50)
    
    # Train model (only first time)
    print("1. Training model...")
    train_alert_model()
    
    # Example: predict your log file
    log_files = ["log1.txt"]
    results = predict_batch_logs_plain_txt(log_files)

    print("\n📋 BATCH PREDICTION SUMMARY:")
    print("="*50)
    for result in results:
        print(f"File: {result['file']}, Line: {result['line']}")
        print(f"Severity: {result['severity']}")
        if result['probabilities']:
            print(f"Confidence: {max(result['probabilities'].values())}%")
        print("-"*30)
