import faiss
import numpy as np

def create_index(embeddings):
    dimension =  embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings))
    return index

def search(index,query_embedding,k=3):
    distances,indices = index.search(np.array([query_embedding]),k)
    return distances[0], indices[0] 