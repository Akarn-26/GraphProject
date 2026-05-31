import streamlit as st
import requests 

st.title("Constitution of Norway QA")
st.caption("Ask anything about the Norwegian Constitution")

question=st.text_input("Your Question")

if st.button("Ask"):
    if question:
        with st.spinnter("Thinking..."):
            response=requests.post("http://localhost:8000/query",json={"query":question})
            answer=response.json()["Answer"]
        st.markdown(answer)
    else:
        st.warning("Please enter a valid question")