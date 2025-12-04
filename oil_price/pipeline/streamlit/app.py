import streamlit as st
import os
import sqlite3
import subprocess
import pandas as pd
import plotly.express as px
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import re

load_dotenv()

DB_PATH = os.getenv("DB_PATH")

# Model - embedder - SentenceTransformer

# Chunki RAG - wypisz informacje o tabeli i przykłady zapytań
rag_chunks = []

# Faiss index - napisz funkcję budującą index (build_faiss_index)
def build_faiss_index(chunks):

    return 

faiss_index, rag_vectors = build_faiss_index(rag_chunks)

# Napisz Funkcję retrieve_context
def retrieve_context(query, k=3):
    return

# Napisz funkcję generate_sql uwzględniającą kontekst RAG
def generate_sql(question: str, context: str):
    return 

# Napisz funkcję sql_firewall
def sql_firewall(sql):
    return 

# Funkcja run_sql
def run_sql(sql):
    return

# Funkcja plot
def plot(df, title):
    return 

# Konfiguracja Streamlit

