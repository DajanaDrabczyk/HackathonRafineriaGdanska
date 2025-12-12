import re
import subprocess
import numpy as np
from sentence_transformers import SentenceTransformer

# Import funkcji z app.py
from app import retrieve_context, build_prompt, table_columns, call_ollama

def generate_sql_with_rag(question: str):
    """
    Pełny pipeline:
    - pobiera kontekst z FAISS (RAG)
    - buduje prompt
    - wysyła do Ollamy
    - zwraca czysty SQL
    """
    ctx = retrieve_context(question)
    prompt = build_prompt(question, ctx, table_columns)
    sql = call_ollama(prompt)
    return sql