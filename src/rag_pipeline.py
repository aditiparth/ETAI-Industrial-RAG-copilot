import requests
import re
from src.config import OPENROUTER_API_KEY, LLM_MODEL, TOP_K_RETRIEVE, TOP_K_FINAL
from src.reranker import rerank

FALLBACK_MODELS = [
    "openai/gpt-oss-20b:free",
    "openai/gpt-oss-120b:free",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "openrouter/free",
]

def call_llm(prompt):
    last_error = None
    for model in FALLBACK_MODELS:
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=60
            )
            data = response.json()

            if "choices" in data and data["choices"]:
                content = data["choices"][0].get("message", {}).get("content")
                if content and content.strip():
                    return content
                last_error = f"Model {model} returned empty/null content"
                continue  # try next fallback model instead of returning empty

            last_error = data
        except Exception as e:
            last_error = str(e)

    raise RuntimeError(f"All fallback models failed. Last error: {last_error}")
PROMPT_TEMPLATE = """You are an industrial knowledge assistant. Answer the question using the context below.
If genuinely nothing in the context is relevant to the question, say "Not found in available documents."
Always cite the source document and page number for each fact you use.

{history}

Context:
{context}

Question: {question}

Answer (with citations in format [Source: filename, Page: X]):"""


def build_context(chunks):
    context_parts = []
    for c in chunks:
        meta = c["metadata"]
        context_parts.append(
            f"[Source: {meta['source']}, Page: {meta['page']}, Type: {meta['doc_type']}]\n{c['text']}"
        )
    return "\n\n---\n\n".join(context_parts)


def build_history_text(chat_history):
    if not chat_history:
        return ""
    recent = chat_history[-4:]  # last 2 exchanges (user+assistant pairs)
    lines = [f"{m['role']}: {m['content'][:200]}" for m in recent]
    return "Previous conversation:\n" + "\n".join(lines)

def rewrite_query_with_history(query, chat_history):
    """Turn a follow-up like 'why did that happen?' into a standalone question
    using recent conversation context, so retrieval has something to search for."""
    if not chat_history:
        return query

    recent = chat_history[-4:]
    history_text = "\n".join(f"{m['role']}: {m['content'][:300]}" for m in recent)

    prompt = f"""Conversation so far:
{history_text}

New user message: "{query}"

Rewrite the new message as a standalone, self-contained question that includes
the specific subject/entity from the conversation (replace words like "that",
"it", "this" with the actual thing being discussed). Output ONLY the rewritten
question, nothing else."""

    try:
        rewritten = call_llm(prompt).strip().strip('"')
        return rewritten if rewritten else query
    except Exception:
        return query

def try_direct_document_match(query, all_chunks):
    """Catch meta-queries like 'summarize the first work order' or 'show me compliance report 3'
    that reference documents by type/position rather than content similarity."""
    query_lower = query.lower()

    doc_type_keywords = {
        "work order": "maintenance",
        "workorder": "maintenance",
        "inspection report": "maintenance",
        "incident report": "maintenance",
        "maintenance schedule": "maintenance",
        "compliance report": "regulatory",
        "compliance audit": "regulatory",
        "audit report": "regulatory",
        "sustainability report": "regulatory",
    }

    matched_type = None
    for kw in sorted(doc_type_keywords, key=len, reverse=True):  # longer phrases first
        if kw in query_lower:
            matched_type = kw
            break

    if not matched_type:
        return None

    candidates = sorted(set(
        c["source"] for c in all_chunks
        if matched_type.replace(" ", "") in c["source"].lower().replace(" ", "").replace("_", "")
    ))

    if not candidates:
        return None

    # word ordinals: "first", "second", "third"...
    word_ordinals = {"first": 0, "1st": 0, "second": 1, "2nd": 1, "third": 2, "3rd": 2,
                      "fourth": 3, "4th": 3, "fifth": 4, "5th": 4}
    for word, idx in word_ordinals.items():
        if re.search(rf"\b{word}\b", query_lower) and idx < len(candidates):
            return candidates[idx]

    # numeric ordinals: "compliance report 3", "report #2", etc.
    numbers = re.findall(r"\b\d+\b", query_lower)
    if numbers:
        idx = int(numbers[0]) - 1  # "report 3" -> index 2
        if 0 <= idx < len(candidates):
            return candidates[idx]

    if len(candidates) == 1:
        return candidates[0]

    return None

def needs_rewrite(query):
    pronouns = ["that", "it", "this", "those", "these", "why did", "how come"]
    return len(query.split()) < 8 and any(p in query.lower() for p in pronouns)


def answer_query(query, hybrid_retriever, kg, all_chunks, chat_history=None,
                  top_k_retrieve=TOP_K_RETRIEVE, top_k_final=TOP_K_FINAL):

    history_text = build_history_text(chat_history)
    # Rewrite follow-up questions into standalone queries for retrieval
    search_query = rewrite_query_with_history(query, chat_history) if needs_rewrite(query) else query

    # --- Path 1: direct document reference ---
    direct_match = try_direct_document_match(search_query, all_chunks)

    # --- Path 1: direct document reference (e.g. "summarize the first work order") ---
    direct_match = try_direct_document_match(query, all_chunks)
    if direct_match:
        matched_chunks = [c for c in all_chunks if c["source"] == direct_match]
        top_chunks = [{
            "chunk_id": c["chunk_id"],
            "text": c["text"],
            "metadata": {"source": c["source"], "page": c["page"], "doc_type": c["doc_type"]},
            "rerank_score": 10.0  # forced high confidence, direct match
        } for c in matched_chunks]

        context = build_context(top_chunks)
        prompt = PROMPT_TEMPLATE.format(history=history_text, context=context, question=query)
        answer_text = call_llm(prompt)

        return {
            "answer": answer_text,
            "sources": [{"source": c["metadata"]["source"], "page": c["metadata"]["page"]} for c in top_chunks],
            "confidence": "High",
            "retrieved_chunks": top_chunks
        }

    # --- Path 2: standard hybrid retrieval + graph augmentation + rerank ---
    candidates = hybrid_retriever.hybrid_search(search_query, top_k=top_k_retrieve)

    mentioned_entities = kg.find_entities_in_query(search_query)
    graph_chunks = []
    for entity in mentioned_entities:
        graph_chunks.extend(kg.get_related_chunks(entity))

    existing_ids = {c["chunk_id"] for c in candidates}
    for gc in graph_chunks:
        if gc["chunk_id"] not in existing_ids:
            candidates.append({
                "chunk_id": gc["chunk_id"],
                "text": gc["text"],
                "metadata": {"source": gc["source"], "page": gc["page"], "doc_type": gc["doc_type"]}
            })
            existing_ids.add(gc["chunk_id"])

    top_chunks = rerank(query, candidates, top_k=top_k_final)

    top_score = top_chunks[0].get("rerank_score", 0) if top_chunks else 0
    confidence = "High" if top_score > 3 else ("Medium" if top_score > 0 else "Low")

    context = build_context(top_chunks)
    prompt = PROMPT_TEMPLATE.format(history=history_text, context=context, question=query)
    answer_text = call_llm(prompt)

    return {
        "answer": answer_text,
        "sources": [{"source": c["metadata"]["source"], "page": c["metadata"]["page"]} for c in top_chunks],
        "confidence": confidence,
        "retrieved_chunks": top_chunks
    }