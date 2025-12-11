0. Srodowisko + .env
1. pipeline/tests/db_test.py
2. ollama install
3. pipeline/ollama/ollama_0.py
4. llm_to_sql_ollama.py - Podaj średnią cenę ropy w 1990 roku
5. llm_to_sql_ollama.py - podaj średnią cenę ropy w 1 kwartale 2010 (dla qwen 1.5 / 14b)
6. llm_to_sql_ollama_v2.py - new prompt - podaj średnią cenę ropy w 1 kwartale 2010
7. llm_to_sql_ollama_v3.py -Ile rekordow, Usun tabele oil_prices, ile rekordow
8. llm_to_sql_ollama_v4.py - system prompt, sql firewall
9. llm_to_sql_ollama_v5.py - wizualizacje
10. llm_to_sql_ollama_v5_rag.py // ollama_rag.py - RAGi
11. streamlit/app.py - pokaź średnie miesięczne ceny ropy w 2010






.....
model="qwen2.5:1.5b-instruct"
model="llama3:latest"
model="qwen2.5:14b"

model="qwen2.5:14b-instruct"
