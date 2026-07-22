import chromadb
from src.embeddings import embed_texts

class VectorStore:
    def __init__(self, collection_name="industrial_docs"):
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.client.get_or_create_collection(collection_name)

    def add_chunks(self, chunks):
        """chunks: list of dicts from chunking.py"""
        texts = [c["text"] for c in chunks]
        ids = [c["chunk_id"] for c in chunks]
        metadatas = [
            {"source": c["source"], "page": c["page"], "doc_type": c["doc_type"]}
            for c in chunks
        ]
        embeddings = embed_texts(texts)
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )

    def query(self, query_text, top_k=15):
        query_embedding = embed_texts([query_text])[0]
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        return self._format_results(results)

    def _format_results(self, results):
        formatted = []
        for i in range(len(results["ids"][0])):
            formatted.append({
                "chunk_id": results["ids"][0][i],
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i]
            })
        return formatted