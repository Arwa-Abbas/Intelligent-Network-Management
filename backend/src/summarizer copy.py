from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from nltk.tokenize import sent_tokenize
from collections import Counter
import numpy as np
import nltk
import re

nltk.download('punkt', quiet=True)

# -----------------------------
# Preprocess and tokenize logs
# -----------------------------
def preprocess_logs(log_text):
    """
    Splits log text into non-empty lines (and optionally sentences).
    """
    lines = log_text.split('\n')
    sentences = [line.strip() for line in lines if line.strip()]
    return sentences

# -----------------------------
# Detect repeated/critical patterns
# -----------------------------
def detect_patterns(sentences, error_keywords=None):
    """
    Detect repeated error/warning/unusual pattern lines.
    Returns a Counter dictionary of line frequencies.
    """
    if error_keywords is None:
        error_keywords = ['error', 'fail', 'connection lost', 'timeout', 'warning']

    # Filter lines containing any critical keyword
    relevant_lines = [line for line in sentences if any(k.lower() in line.lower() for k in error_keywords)]
    line_counts = Counter(relevant_lines)
    return line_counts

# -----------------------------
# Compute TF-IDF sentence scores
# -----------------------------
def compute_tfidf_scores(sentences):
    """
    Converts sentences into TF-IDF vectors and computes sentence importance scores.
    """
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(sentences)
    sentence_scores = np.array(tfidf_matrix.sum(axis=1)).ravel()
    return sentence_scores, tfidf_matrix

# -----------------------------
# Cluster similar sentences
# -----------------------------
def cluster_sentences(tfidf_matrix, sentences, num_clusters=10):
    """
    Groups similar sentences using KMeans clustering.
    Returns a dictionary of clusters with sentence indices.
    """
    num_clusters = min(num_clusters, len(sentences))
    kmeans = KMeans(n_clusters=num_clusters, random_state=42)
    kmeans.fit(tfidf_matrix)
    
    clusters = {i: [] for i in range(num_clusters)}
    for idx, label in enumerate(kmeans.labels_):
        clusters[label].append(idx)  # store indices, not sentences
    return clusters

# -----------------------------
# Select representative sentence from each cluster
# -----------------------------
def select_representatives(sentences, sentence_scores, clusters, line_counts):
    """
    From each cluster, select the most important sentence.
    Importance = TF-IDF score + repeated critical line weight.
    """
    rep_indices = []
    for cluster_id, indices in clusters.items():
        # Boost repeated critical lines
        cluster_scores = []
        for idx in indices:
            score = sentence_scores[idx]
            if sentences[idx] in line_counts:
                score += line_counts[sentences[idx]]  # boost repeated critical lines
            cluster_scores.append((score, idx))
        # Pick sentence with max score in cluster
        best_sentence_idx = max(cluster_scores)[1]
        rep_indices.append(best_sentence_idx)
    return rep_indices

# -----------------------------
# Rank top representatives for summary
# -----------------------------
def rank_top_sentences(sentences, sentence_scores, line_counts, rep_indices, n_sentences=5):
    """
    Rank representative sentences and pick top N for final summary.
    """
    final_scores = []
    for idx in rep_indices:
        score = sentence_scores[idx]
        if sentences[idx] in line_counts:
            score += line_counts[sentences[idx]]  # boost repeated critical lines
        final_scores.append((score, idx))
    
    # Sort by score descending
    final_scores.sort(reverse=True)
    
    # Pick top n_sentences
    top_indices = [idx for score, idx in final_scores[:n_sentences]]
    top_indices.sort()  # maintain original order in summary
    return top_indices

# -----------------------------
# Full summarization pipeline
# -----------------------------
def summarize_log(log_text, n_sentences=5, num_clusters=10):
    """
    Full pipeline:
    1. Preprocess logs
    2. Detect repeated/critical patterns
    3. TF-IDF scoring
    4. Cluster similar sentences
    5. Select representative from each cluster
    6. Rank top representatives
    7. Build final summary
    """

    sentences = preprocess_logs(log_text)
    if len(sentences) <= n_sentences:
        return log_text  

    line_counts = detect_patterns(sentences)

    sentence_scores, tfidf_matrix = compute_tfidf_scores(sentences)
    
    clusters = cluster_sentences(tfidf_matrix, sentences, num_clusters=num_clusters)

    rep_indices = select_representatives(sentences, sentence_scores, clusters, line_counts)

    top_indices = rank_top_sentences(sentences, sentence_scores, line_counts, rep_indices, n_sentences=n_sentences)
    
    summary = ' '.join([sentences[i] for i in top_indices])
    return summary


if __name__ == "__main__":
    with open("log2_50K.txt", "r") as file:
        log_text = file.read()
    
    summary = summarize_log(log_text, n_sentences=5, num_clusters=5)
    print("==== LOG SUMMARY ====")
    print(summary)
