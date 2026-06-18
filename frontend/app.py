import streamlit as st
import requests
import pandas as pd

BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(
page_title="RAG Q&A System",
page_icon="📄",
layout="centered"
)

st.title("📄 RAG Q&A System")
st.markdown("Ask questions from uploaded PDF documents using Retrieval Augmented Generation.")


with st.sidebar:
    st.header("Upload Document")

    uploaded_file = st.file_uploader("Choose a PDF file",type=["pdf"])

    if uploaded_file is not None:

        if st.button("Ingest Document"):

            files = {
                "file": (
                    uploaded_file.name,
                    uploaded_file,
                    "application/pdf"
                )
            }

            response = requests.post(f"{BASE_URL}/ingest",files=files)

            if response.status_code == 202:
                st.success("Document uploaded successfully.")
            else:
                st.error("Failed to ingest document.")




question = st.chat_input("Enter your question")
 

if question:
        

        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
             with st.spinner("Searching document..."):
                  response = requests.post(f"{BASE_URL}/ask",json={"question": question})
                  data = response.json()
        st.markdown(data["answer"])

        st.subheader("Sources")

        for source in data["sources"]:

            with st.expander(f"Chunk {source['chunk_id']}"):
                st.write(source["text"])


st.divider()


with st.sidebar:
    st.header("Analytics")

    
    response = requests.get(f"{BASE_URL}/analytics")

    analytics = response.json()

    col1, col2, col3 = st.columns(3)

    with col1:
            st.metric(
            "Total Queries",
            analytics["total_queries"]
        )
    with col2:
            st.metric(
            "Successful Answers",
            analytics["successful_answers"]
            )

    with col1:
            st.metric(
            "Average Response Time",
            analytics["avarage_response_time"]
            )
    with col2:
            st.metric(
                "Failed Answers",
                analytics["failed_answers"]
            )
    


        
    st.metric(
        "Success Rate",
        f"{analytics['sucess_rate']}%"
        )
    
    

    top_questions_df = pd.DataFrame(analytics["top_questions"])

    st.subheader("Most Frequently Asked Questions")
    st.table(pd.DataFrame(analytics["top_questions"]))
    
    failed_queries_df = pd.DataFrame(analytics["failed_queries"],columns=["Question"])

    st.subheader("Queries With No Answer Found")
    st.table(pd.DataFrame(analytics["failed_queries"],columns=["Question"]))
         
        

