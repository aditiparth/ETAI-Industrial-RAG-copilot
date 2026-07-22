from rank_bm25 import BM25Okapi
import re

class HybridRetriever:
    def __init__(self, vectorstore, all_chunks):
        self.vectorstore = vectorstore
        self.all_chunks = all_chunks
        self.chunk_texts = [c["text"] for c in all_chunks]
        self.tokenized_corpus = [self._tokenize(t) for t in self.chunk_texts]
        self.bm25 = BM25Okapi(self.tokenized_corpus)

    def _tokenize(self, text):
        return re.findall(r"\w+", text.lower())

    def bm25_search(self, query, top_k=15):
        tokenized_query = self._tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)
        ranked_idx = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        results = []
        for idx in ranked_idx:
            if scores[idx] > 0:
                results.append({
                    "chunk_id": self.all_chunks[idx]["chunk_id"],
                    "text": self.all_chunks[idx]["text"],
                    "metadata": {
                        "source": self.all_chunks[idx]["source"],
                        "page": self.all_chunks[idx]["page"],
                        "doc_type": self.all_chunks[idx]["doc_type"]
                    },
                    "bm25_score": float(scores[idx])
                })
        return results

    def hybrid_search(self, query, top_k=15):
        vector_results = self.vectorstore.query(query, top_k=top_k)
        bm25_results = self.bm25_search(query, top_k=top_k)

        merged = {}
        for r in vector_results:
            merged[r["chunk_id"]] = r
        for r in bm25_results:
            if r["chunk_id"] in merged:
                merged[r["chunk_id"]]["bm25_score"] = r["bm25_score"]
            else:
                merged[r["chunk_id"]] = r

        return list(merged.values())