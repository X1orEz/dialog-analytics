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
- [ ] LLM-разметка
- [ ] FastAPI + Dockerfile
- [ ] ETL и дашборд

## Быстрый старт
cp .env.example .env
docker compose up -d
python -m src.generate_data
python -m src.db
