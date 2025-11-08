import streamlit as st
import requests

# Backend API URL
BACKEND_URL = "http://127.0.0.1:5000"

st.title("Intelligent Network Management Dashboard")

# Create tabs for different functionality
tab1, tab2, tab3 = st.tabs(["Classify Alert", "Summarize Logs", "Chatbot"])

# -------------------------------
# Tab 1: Alert Classification
# -------------------------------
with tab1:
    st.header("Alert Classification")
    alert = st.text_area("Enter network alert")

    if st.button("Classify Alert"):
        if alert:
            response = requests.post(
                f"{BACKEND_URL}/classify",
                json={"log_text": alert}  # match backend key
            )
            result = response.json()
            st.success(f"Classification: {result['classification']}")
        else:
            st.warning("Please enter an alert text.")

# -------------------------------
# Tab 2: Log Summarization
# -------------------------------
with tab2:
    st.header("Log Summarization")
    log_text = st.text_area("Enter raw network logs or paste log text here")

    if st.button("Summarize Logs"):
        if log_text:
            response = requests.post(
                f"{BACKEND_URL}/summarize",
                json={"log_text": log_text}  # match backend key
            )
            result = response.json()
            st.subheader("Summary")
            st.write(result["summary"])
        else:
            st.warning("Please enter log text to summarize.")

# -------------------------------
# Tab 3: Chatbot
# -------------------------------
with tab3:
    st.header("Chatbot")
    user_message = st.text_input("Ask the network chatbot a question:")

    if st.button("Send Message"):
        if user_message:
            response = requests.post(
                f"{BACKEND_URL}/chat",
                json={"message": user_message}
            )
            result = response.json()
            st.write(f"Bot: {result['response']}")
        else:
            st.warning("Please enter a message.")
