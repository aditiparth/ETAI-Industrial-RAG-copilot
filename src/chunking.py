import fitz  # pymupdf
import re
import os

def load_pdf_text(filepath):
    """Extract text page by page, preserving page numbers for citation."""
    doc = fitz.open(filepath)
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text()
        if text.strip():
            pages.append({"page": i + 1, "text": text})
    doc.close()
    return pages

def load_txt(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return [{"page": 1, "text": f.read()}]

def chunk_text(text, chunk_size=400, overlap=80):
    """Simple word-based chunking with overlap."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks

def process_document(filepath, doc_type):
    """
    doc_type: 'regulatory', 'technical', 'maintenance'
    Returns list of dicts: {text, source, page, doc_type, chunk_id}
    """
    ext = filepath.split(".")[-1].lower()
    if ext == "pdf":
        pages = load_pdf_text(filepath)
    else:
        pages = load_txt(filepath)

    filename = os.path.basename(filepath)
    all_chunks = []
    chunk_counter = 0
    for page_data in pages:
        chunks = chunk_text(page_data["text"])
        for c in chunks:
            all_chunks.append({
                "text": c,
                "source": filename,
                "page": page_data["page"],
                "doc_type": doc_type,
                "chunk_id": f"{filename}_{chunk_counter}"
            })
            chunk_counter += 1
    return all_chunks

def process_all_documents(folder_path, doc_type_map):
    """
    doc_type_map: dict mapping filename -> doc_type
    e.g. {"oisd_std.pdf": "regulatory", "workorder_1.txt": "maintenance"}
    """
    all_chunks = []
    for filename, doc_type in doc_type_map.items():
        filepath = os.path.join(folder_path, filename)
        if os.path.exists(filepath):
            chunks = process_document(filepath, doc_type)
            all_chunks.extend(chunks)
            print(f"Processed {filename}: {len(chunks)} chunks")
        else:
            print(f"WARNING: {filepath} not found")
    return all_chunks