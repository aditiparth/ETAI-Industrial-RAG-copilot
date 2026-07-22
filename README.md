# 🏭 ETAI Copilot – AI for Industrial Knowledge Intelligence

> **Turning fragmented industrial documents into a unified operational intelligence platform.**

ETAI Copilot is an AI-powered Industrial Knowledge Intelligence platform that enables organizations to query, connect, and understand engineering knowledge spread across thousands of heterogeneous documents. By combining **Retrieval-Augmented Generation (RAG)**, **Knowledge Graphs**, **Hybrid Search**, and **Large Language Models**, ETAI transforms scattered documentation into an intelligent assistant for engineers, maintenance teams, and plant operators.

---

## 📌 Problem Statement

Industrial organizations manage massive volumes of documentation including:

- Engineering drawings (P&IDs)
- Standard Operating Procedures (SOPs)
- Maintenance work orders
- Inspection reports
- Safety manuals
- Regulatory documents
- Equipment manuals
- Incident reports

These documents are often stored across multiple disconnected systems, making information retrieval slow, error-prone, and dependent on individual experience.

As a result:

- Engineers spend significant time searching for information.
- Critical operational knowledge becomes siloed.
- Maintenance decisions are made without complete context.
- Compliance audits require extensive manual effort.
- Valuable institutional knowledge is lost as experienced engineers retire.

ETAI Copilot addresses these challenges by creating a unified, searchable knowledge layer over enterprise documentation.

---

# 🚀 Features

### 📄 Universal Document Ingestion

Upload and process industrial documents including:

- PDF manuals
- Engineering reports
- SOPs
- Maintenance records
- Text documents

The system automatically extracts relevant content for downstream processing.

---

### 🧠 Intelligent Entity Extraction

Automatically identifies industrial entities such as:

- Equipment IDs
- Pump and valve tags
- Safety standards
- Organizations
- Dates
- Locations
- Personnel

using **spaCy Named Entity Recognition** combined with custom industrial pattern matching.

---

### 🔗 Knowledge Graph Generation

Builds an interconnected knowledge graph linking:

- Documents
- Equipment
- Standards
- Organizations
- Dates
- Operational relationships

allowing users to explore hidden connections across the entire document corpus.

---

### 🔍 Hybrid Retrieval

Instead of relying on a single search technique, ETAI combines:

- Semantic Search (Sentence Transformers)
- BM25 Keyword Search
- Knowledge Graph Traversal

This significantly improves retrieval quality for industrial queries.

---

### 🎯 Cross-Encoder Re-ranking

Retrieved documents are re-ranked using a Cross-Encoder model to ensure the most relevant context is sent to the language model.

This improves precision and reduces irrelevant responses.

---

### 💬 Conversational Industrial Copilot

Ask natural language questions like:

> Which safety standards apply to Pump P-101?

> Show maintenance history of Compressor C-202.

> What inspection procedures mention pressure valves?

The assistant responds with:

- Accurate answers
- Source citations
- Page numbers
- Confidence score
- Supporting document context

---

### 🌐 Interactive Knowledge Graph

Visualize relationships between:

- Equipment
- Documents
- Safety standards
- Organizations
- Engineers

using an interactive graph interface powered by Neo4j and PyVis.

---

## 🏗️ System Architecture

```
                  <img width="621" height="667" alt="image" src="https://github.com/user-attachments/assets/d38aca7e-745e-41ba-b6bf-bfa81495791f" />

```

---

# ⚙️ Tech Stack

| Component | Technology |
|------------|------------|
| Frontend | Streamlit |
| Document Processing | PyMuPDF |
| NLP | spaCy |
| Custom Entity Detection | Regex + Pattern Matching |
| Embeddings | Sentence Transformers |
| Vector Database | ChromaDB |
| Keyword Retrieval | BM25 |
| Re-ranking | Cross Encoder |
| Knowledge Graph | Neo4j |
| Graph Visualization | PyVis |
| LLM | OpenRouter (Open-source models) |

---

# 📂 Project Workflow

### 1. Upload Documents

Industrial PDFs and text files are uploaded into the platform.

↓

### 2. Document Processing

Documents are:

- Parsed
- Chunked
- Cleaned
- Indexed

↓

### 3. Entity Extraction

Industrial entities are automatically detected.

↓

### 4. Knowledge Graph Construction

Relationships between entities are stored in Neo4j.

↓

### 5. Vector Index Creation

Text chunks are embedded and stored inside ChromaDB.

↓

### 6. User Query

A natural language query is received.

↓

### 7. Hybrid Retrieval

The system performs:

- BM25 search
- Semantic search
- Knowledge graph traversal

↓

### 8. Re-ranking

Top retrieved chunks are re-ranked using a Cross Encoder.

↓

### 9. AI Response

The LLM generates a grounded answer using retrieved context while providing citations and confidence scores.

---

# 💡 Why Hybrid Retrieval?

Traditional RAG retrieves documents based only on semantic similarity.

ETAI combines three complementary retrieval strategies:

- **BM25** for exact equipment IDs and standards
- **Semantic Search** for conceptual similarity
- **Knowledge Graph Traversal** for discovering related operational information

This results in higher retrieval accuracy and richer contextual understanding.

---

# 🌟 Key Advantages

- Explainable AI responses with citations
- Interactive knowledge graph visualization
- Reduced document search time
- Improved operational knowledge discovery
- Better maintenance decision support
- Organizational knowledge retention
- Easy deployment using open-source technologies

---

# 🎯 Potential Use Cases

- Industrial Asset Management
- Preventive Maintenance
- Root Cause Analysis
- Compliance Audits
- Safety Management
- Knowledge Retention
- Technical Documentation Search
- Plant Operations Support

---

# 📸 Demo

### Chat Interface

*(Add screenshot here)*

---

### Knowledge Graph

*(Add screenshot here)*

---

### Document Upload

*(Add screenshot here)*

---

# 📈 Future Roadmap

- Support for engineering drawings (P&IDs)
- OCR for scanned documents
- Real-time IoT integration
- Predictive maintenance recommendations
- Root Cause Analysis agent
- Compliance gap detection
- Multi-agent industrial workflows
- SAP / CMMS integration
- Mobile application for field engineers

---

# 🤝 Team

Developed as part of an Industrial AI Hackathon to demonstrate how Retrieval-Augmented Generation and Knowledge Graphs can transform enterprise knowledge management.

---

# 📜 License

This project is intended for educational and hackathon purposes.

---

## ⭐ If you found this project interesting, consider giving it a star!
