def classify_log(log_text):
    if "error" in log_text.lower():
        return "ALERT: Error detected!"
    elif "warning" in log_text.lower():
        return "Warning log."
    else:
        return "Normal log."
