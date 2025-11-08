from flask import Flask, request, jsonify
from flask_cors import CORS
from summarizer import summarize_log
from classifier import classify_log
from chatbot import chatbot_response

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return jsonify({"message": "Backend is running"})

@app.route('/summarize', methods=['POST'])
def summarize():
    data = request.get_json()
    text = data.get("log_text", "")
    summary = summarize_log(text)
    return jsonify({"summary": summary})

@app.route('/classify', methods=['POST'])
def classify():
    data = request.get_json()
    text = data.get("log_text", "")
    result = classify_log(text)
    return jsonify({"classification": result})

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    message = data.get("message", "")
    response = chatbot_response(message)
    return jsonify({"response": response})

if __name__ == '__main__':
    app.run(debug=True)
