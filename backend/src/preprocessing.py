import re

def clean_log_text(log_text):
    # Remove timestamps and symbols
    cleaned = re.sub(r'\[.*?\]', '', log_text)
    cleaned = re.sub(r'[^a-zA-Z0-9\s\.\-]', '', cleaned)
    return cleaned.strip()
