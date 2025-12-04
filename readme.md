# Instrukcja uruchomienia środowiska LLM → SQL na Linuxie

Poniższy przewodnik przeprowadza przez instalację Minicondy, konfigurację środowiska, testy bazy danych, instalację Ollama oraz uruchamianie kolejnych wersji skryptów LLM-to-SQL.

0. Instalacja Minicondy (Linux)

Pobierz instalator:

```bash
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
```

Uruchom instalator:

```bash
bash Miniconda3-latest-Linux-x86_64.sh
```

Sprawdź poprawność instalacji:

```bash
conda --version
```

1. Tworzenie środowiska + zmienne .env

Upewnij się, że w katalogu znajduje się plik `environment.yml`, a następnie wykonaj:

```bash
conda env create -f environment.yml
conda activate llm2sql
```

Utwórz plik `.env`, np.:

```bash
DB_PATH=oil_prices.db
```

2. Test połączenia z bazą danych

Uruchom test:

```bash
python pipeline/tests/db_test.py
```

3. Instalacja i weryfikacja Ollama

Instalacja (Linux):

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Sprawdzenie wersji:

```bash
ollama --version
```

## Lista modeli:

```bash
ollama list
```

4. Pierwszy model: Qwen 1.5B

Pobranie:

ollama pull qwen2.5:1.5b-instruct


Test:

python pipeline/ollama/ollama_0.py

5. Pierwsze zapytanie LLM → SQL

Uruchom:

python llm_to_sql_ollama.py


Przykładowy prompt:

Podaj średnią cenę ropy w 1990 roku.

6. Zapytanie kwartalne — Qwen 1.5B lub 14B

Pobranie większego modelu:

ollama pull qwen2.5:14b // sqlcoder:latest


Prompt:

Podaj średnią cenę ropy w 1 kwartale 2010.

7. Wersja 2 — nowy prompt
python llm_to_sql_ollama_v2.py

8. Wersja 3 — operacje na DB
python llm_to_sql_ollama_v3.py


Przykłady:

"Ile jest rekordów?"

"Usuń tabelę oil_prices."

9. Wersja 4 — system prompt + SQL Firewall
python llm_to_sql_ollama_v4.py

10. Wersja 5 — wizualizacje
python llm_to_sql_ollama_v5.py

11. Wersja 5 + RAG
python llm_to_sql_ollama_v5_rag.py
# lub
python ollama_rag.py

12. Aplikacja Streamlit

Uruchom:

```bash
streamlit run streamlit/app.py
```

Przykład promptu:

Pokaż średnie miesięczne ceny ropy w 2010 roku.

## Modele stosowane w kursie

Można je pobrać poleceniem ollama pull <model>:

qwen2.5:1.5b-instruct
qwen2.5:1.5b
qwen2.5:14b
qwen2.5:14b-instruct
llama3:latest
sqlcode:latest

