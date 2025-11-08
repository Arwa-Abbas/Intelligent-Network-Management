from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.tokenize import sent_tokenize
import numpy as np
import nltk

nltk.download('punkt', quiet=True)

def summarize_log(log_text, n_sentences=2):
    sentences = sent_tokenize(log_text)
    if len(sentences) <= n_sentences:
        return log_text
    
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(sentences)
    sentence_scores = np.array(tfidf_matrix.sum(axis=1)).ravel()
    
    top_sentence_indices = sentence_scores.argsort()[-n_sentences:][::-1]
    summary = ' '.join([sentences[i] for i in sorted(top_sentence_indices)])
    return summary

