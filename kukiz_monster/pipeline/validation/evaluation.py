import json
from difflib import SequenceMatcher
import os
from dotenv import load_dotenv
import re

load_dotenv()

gold_path = os.getenv("GOLD_PATH")

def sql_similarity(a, b):
    """Liczy podobieństwo SQL (string similarity)."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def evaluate_model(gold_path, model_fn):
    """
    gold_path – ścieżka do gold_dataset.json
    model_fn(question) – funkcja generująca SQL z pytania (np. ollama generator)
    """

    with open(gold_path, "r") as f:
        dataset = json.load(f)

    correct = 0
    total = len(dataset)
    similarities = []

    for item in dataset:
        q = item["question"]
        expected = item["expected_sql"].strip()

        predicted = model_fn(q).strip()

        sim = sql_similarity(predicted, expected)
        similarities.append(sim)

        if sim > 0.85:  # SQL bardzo podobny
            correct += 1

    precision = correct / total
    recall = precision      # w NL→SQL precision = recall przy pełnym dataset
    accuracy = precision

    return {
        "precision": precision,
        "recall": recall,
        "accuracy": accuracy,
        "avg_similarity": sum(similarities) / len(similarities)
    }
