import streamlit as st
import os
import tempfile
from src.chunking import process_all_documents, process_document
from src.vectorstore import VectorStore
from src.hybrid_retrieval import HybridRetriever
from src.entity_extraction import extract_entities_from_chunks
from src.knowledge_graph import KnowledgeGraph
from src.rag_pipeline import answer_query
from src.graph_viz import render_knowledge_graph, render_legend_html
import streamlit.components.v1 as components

st.set_page_config(page_title="Industrial Knowledge Copilot", layout="wide")
st.title("Industrial Knowledge Intelligence Copilot")

doc_type_map = {
    "4905_9_SustainabilityReport_13.pdf": "regulatory",
    "ESG at NTPC - March 2024.pdf": "regulatory",
    "IndianOil_BRSR2425.pdf": "regulatory",
    "IndianOilBRSR222301082023.pdf": "regulatory",
    "Sustainability Data Trend 2024.pdf": "regulatory",
    "Sustainability Data Trends FY 2023-24.pdf": "regulatory",
    "workorder_001.txt": "maintenance",
    "workorder_002.txt": "maintenance",
    "inspection_report_001.txt": "maintenance",
    "inspection_report_002.txt": "maintenance",
    "incident_report_001.txt": "maintenance",
    "maintenance_schedule_001.txt": "maintenance",
}

@st.cache_resource
def initialize_base_pipeline():
    """Loads the original fixed document set once, cached across the app's lifetime."""
    chunks = process_all_documents("data/raw_docs", doc_type_map)
    chunks = extract_entities_from_chunks(chunks)

    vs = VectorStore()
    vs.add_chunks(chunks)

    kg = KnowledgeGraph()
    kg.clear_graph()
    kg.add_chunks_batch(chunks)

    return vs, kg, chunks

with st.spinner("Loading base knowledge base... (first load takes a minute or two)"):
    base_vs, base_kg, base_chunks = initialize_base_pipeline()

# session state holds the FULL current corpus (base + any uploads this session)
if "all_chunks" not in st.session_state:
    st.session_state.all_chunks = list(base_chunks)
if "retriever" not in st.session_state:
    st.session_state.retriever = HybridRetriever(base_vs, st.session_state.all_chunks)
if "messages" not in st.session_state:
    st.session_state.messages = []

st.success(f"Knowledge base ready — {len(set(c['source'] for c in st.session_state.all_chunks))} documents loaded.")

# --- Sidebar: upload new documents ---
with st.sidebar:
    st.header("📄 Upload New Documents")
    doc_type = st.selectbox("Document type", ["regulatory", "technical", "maintenance"])
    uploaded_files = st.file_uploader(
        "Upload PDF or TXT files", type=["pdf", "txt"], accept_multiple_files=True
    )

    if uploaded_files and st.button("Ingest documents"):
        with st.spinner("Processing and ingesting..."):
            new_chunks = []
            for uploaded_file in uploaded_files:
                suffix = "." + uploaded_file.name.split(".")[-1]
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(uploaded_file.read())
                    tmp_path = tmp.name

                chunks = process_document(tmp_path, doc_type)
                for c in chunks:
                    c["source"] = uploaded_file.name
                    c["chunk_id"] = f"{uploaded_file.name}_{c['chunk_id'].split('_')[-1]}"

                chunks = extract_entities_from_chunks(chunks)
                new_chunks.extend(chunks)
                os.unlink(tmp_path)

            # add to the base vector store (persists across the session)
            base_vs.add_chunks(new_chunks)

            # add to the knowledge graph
            base_kg.add_chunks_batch(new_chunks)

            # update the full in-memory chunk list and rebuild BM25
            st.session_state.all_chunks.extend(new_chunks)
            st.session_state.retriever = HybridRetriever(base_vs, st.session_state.all_chunks)

            # invalidate cached graph views so newly uploaded docs show up
            for key in list(st.session_state.keys()):
                if key.startswith("graph_html_"):
                    del st.session_state[key]

        st.success(f"Ingested {len(uploaded_files)} document(s). Total chunks: {len(st.session_state.all_chunks)}")

    st.divider()
    st.caption(f"📚 Documents: {len(set(c['source'] for c in st.session_state.all_chunks))}")
    st.caption(f"🧩 Chunks: {len(st.session_state.all_chunks)}")

# --- Tabs: Chat and Knowledge Graph ---
tab1, tab2 = st.tabs(["💬 Chat", "🕸️ Knowledge Graph"])

with tab1:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    query = st.chat_input("Ask about equipment, maintenance, or compliance...")

    if query:
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.write(query)

        with st.chat_message("assistant"):
            with st.spinner("Searching knowledge base..."):
                try:
                    result = answer_query(
                        query,
                        st.session_state.retriever,
                        base_kg,
                        st.session_state.all_chunks,
                        chat_history=st.session_state.messages
                    )
                except Exception as e:
                    st.error(f"Something went wrong generating a response: {e}")
                    st.stop()

            st.write(result["answer"])
            st.caption(f"Confidence: {result['confidence']}")
            if result['confidence'] == "Low":
                st.info("💡 I wasn't fully confident in this answer — the available documents may not directly cover this. Try rephrasing, or check the Sources below to see what I actually searched.")
            with st.expander("Sources"):
                for s in result["sources"]:
                    st.write(f"- {s['source']}, page {s['page']}")

        st.session_state.messages.append({"role": "assistant", "content": result["answer"]})

with tab2:
    st.subheader("Live Knowledge Graph")
    st.caption("Documents connected to the equipment and standards they reference")

    filter_options = st.multiselect(
        "Filter by document type",
        options=["regulatory", "maintenance", "technical"],
        default=["maintenance", "technical"]
    )

    if st.button("Refresh graph"):
        for key in list(st.session_state.keys()):
            if key.startswith("graph_html_"):
                del st.session_state[key]

    cache_key = f"graph_html_{'_'.join(sorted(filter_options))}"
    if cache_key not in st.session_state:
        with st.spinner("Building graph visualization..."):
            graph_data = base_kg.get_graph_data(limit=300)
            st.session_state[cache_key] = render_knowledge_graph(graph_data, doc_type_filter=filter_options)

    st.markdown(render_legend_html(), unsafe_allow_html=True)
    components.html(st.session_state[cache_key], height=670)