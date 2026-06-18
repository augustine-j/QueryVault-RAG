from pypdf import PdfReader
from app.chunker import chunk_text
from app.embeddings import create_embeddings,model
from app.vector_store import create_index,search
from app.rag import ask_llm

class RAGService:

    def __init__(self):
        self.chunks = []
        self.index = None

    def ingest_pdf(self,pdf_path):
        reader = PdfReader(pdf_path)
        text =""
        
        for page in reader.pages:
            text+= page.extract_text()+"\n"
        
        self.chunks = chunk_text(text,chunk_size=1000,overlap=100) 
        embeddings = create_embeddings(self.chunks)
        self.index = create_index(embeddings)
        print(f"Loaded {len(self.chunks)} chunks")


    def ask(self,question):

        if self.index is None:
            return{
                "answer":"No document has been uploaded yet.",
                "sources":[]
            }

        query_embedding = model.encode(question)

        distances,results = search(self.index,query_embedding,k=5)
        context =""
        for item in results:
            context+=self.chunks[item] + "\n\n"
        answer = ask_llm(question,context)

        sources = []
        for items in results:
            sources.append({
                "chunk_id":int(items),
                "text":self.chunks[items]
            })

        return {
            "answer":answer,
            "sources":sources
        }
