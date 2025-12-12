import streamlit as st
from evaluation import evaluate_model
import json
import os
import sys
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(BASE_DIR)
from sql_pipeline import generate_sql_with_rag
def model_sql_fn(question):
    return generate_sql_with_rag(question)
st.title("Ewaluacja modelu NL→SQL")
gold_path = "gold_dataset.json"
if st.button("Uruchom ewaluację"):
    results = evaluate_model(gold_path, model_sql_fn)
    st.subheader("Wyniki")
    st.metric("Precision", f"{results['precision']:.2f}")
    st.metric("Recall", f"{results['recall']:.2f}")
    st.metric("Accuracy", f"{results['accuracy']:.2f}")
    st.metric("Avg SQL Similarity", f"{results['avg_similarity']:.2f}")