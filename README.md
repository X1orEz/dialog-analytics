# Dialog Analytics

End-to-end сервис анализа диалогов поддержки: SQL → pandas → LLM-разметка → метрики → FastAPI → дашборд.

Стек: Python, PostgreSQL, Docker, FastAPI, LLM API, Streamlit.

## Статус
- [x] Структура репозитория
- [x] PostgreSQL в Docker Compose
- [x] Схема БД
- [x] Генерация синтетических данных
- [x] Загрузка данных в БД
- [x] SQL-запросы и метрики
- [x] EDA-ноутбук
- [x] Метрики в `src/metrics.py`
- [x] Статистика и A/B (`src/stats.py`)
- [x] ML-метрики (`src/evaluate.py`)
- [x] LLM-разметка
- [ ] FastAPI + Dockerfile
- [ ] ETL и дашборд

## Быстрый старт
1. Клонируй репозиторий и перейди в него:
   ```bash
   git clone https://github.com/X1orEz/dialog-analytics.git
   cd dialog-analytics

2. Скопируй переменные окружения: 
    cp .env.example .env

3. Установи Ollama и модель (один раз):
    curl -fsSL https://ollama.com/install.sh | sh
    ollama pull llama3.2:3b

4. Подними Postgres и установи зависимости:
    docker compose up -d
    python -m pip install -r requirements.txt
    python -m pip install -e .

5. Загрузи данные и запусти разметку:
    python -m src.generate_data
    python -m src.db
    python -m src.labeling
