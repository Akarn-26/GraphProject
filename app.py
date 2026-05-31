import streamlit as st
import requests
from dotenv import load_dotenv
import os
load_dotenv()

API_URL = os.getenv("API_URL", "http://localhost:8000")

def get_health():
    try:
        return requests.get(f"{API_URL}/health", timeout=60).json()
    except:
        return {"status": "unavailable"}

st.set_page_config(page_title="Norway Constitution QA", page_icon="🏛️")
st.title("🏛️ Norwegian Constitution QA")
st.caption("Ask anything about Norway's 1814 constitution")

with st.spinner("Checking system status..."):
    health = get_health()
    if health.get("status") != "ready":
        st.error("API or Neo4j is offline. Make sure both servers are running.")
        st.stop()

question = st.text_input("Your question")

if st.button("Ask", type="primary"):
    if question:
        with st.spinner("Thinking..."):
            try:
                response = requests.post(
                    f"{API_URL}/query",
                    json={"query": question},
                    timeout=30
                )
                st.markdown(response.json()["Answer"])
            except Exception as e:
                st.error("Something went wrong. Please try again.")
    else:
        st.warning("Please enter a question")