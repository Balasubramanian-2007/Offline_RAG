Offline RAG System for Technical Document Retrieval
An end-to-end offline Retrieval-Augmented Generation (RAG) system that allows users to upload documents (PDF/Word) and ask technical questions with accurate, context-grounded answers — without internet dependency.Built using semantic embeddings, vector search, and local language models.

Why Offline RAG?
 -Works in restricted networks
 -No API cost
 -Data privacy
 -Low latency
 -Ideal for enterprises and research environments

Features :
 -Upload PDF and DOCX technical documents
 -Structure-aware chunking based on document headings
 -Semantic embedding using Sentence Transformers
 -Fast similarity search using FAISS vector index
 -Context-grounded question answering (no hallucinations)
 -REST API built with FastAPI
 -Lightweight database storage (SQLite / PostgreSQL supported)
 -Works fully offline after setup

System Architecture :
 -Document upload → chunking based on structure
 -Chunks converted into vector embeddings
 -Embeddings stored in FAISS index
 -User query embedded and searched against vectors
 -Most relevant chunks retrieved
 -Answer generated strictly from retrieved context

Tech Stack
 -Python
 -FastAPI
 -FAISS
 -Sentence Transformers
 -SQLite / PostgreSQL
 -Local LLM / API-based LLM (pluggable)

