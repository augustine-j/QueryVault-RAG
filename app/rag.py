import requests

def ask_llm(question,context):
    prompt = f"""You are a document assistant.
    Answer ONLY from the provided context.
    If the answer is not present in the context, reply exactly:
    I could not find the answer in the document.
    Provide a concise answer.
    
    Context:{context}
    Question:{question}
    Answer:
    """

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model":"llama3.2:3b",
            "prompt":prompt,
            "stream":False
        }
    )

    return response.json()["response"]