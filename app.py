import streamlit as st
import requests

st.set_page_config(page_title="Norway Constitution QA", page_icon="🏛️")

st.title("🏛️ Norwegian Constitution QA")
st.caption("Ask anything about Norway's 1814 constitution")

def get_health():
    try:
        return requests.get("http://localhost:8000/health", timeout=2).json()
    except:
        return {"status": "unavailable", "embedding_model": False, "neo4j": False}

if "ready" not in st.session_state:
    with st.spinner("Checking system status..."):
        health = get_health()
        st.session_state.ready = health.get("status") == "ready"
        if not st.session_state.ready:
            st.error("API or Neo4j is offline. Make sure both servers are running.")
            st.stop()

question = st.text_input("Your question")

if st.button("Ask", type="primary"):
    if question:
        with st.spinner("Thinking..."):
            try:
                response = requests.post(
                    "http://localhost:8000/query",
                    json={"query": question},
                    timeout=30
                )
                st.markdown(response.json()["Answer"])
            except Exception as e:
                st.error("Something went wrong. Please try again.")
    else:
        st.warning("Please enter a question")