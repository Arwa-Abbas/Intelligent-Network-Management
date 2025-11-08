from summarizer import summarize_log
from classifier import classify_log

def chatbot_response(message):
    message = message.lower()
    if "summarize" in message:
        return "Please provide the log text you want summarized."
    elif "classify" in message:
        return "Send me a log entry, and I’ll classify it."
    elif "hello" in message or "hi" in message:
        return "Hello! I can summarize or classify logs for you."
    else:
        return "I’m not sure how to respond. Try saying 'summarize logs' or 'classify log'."
