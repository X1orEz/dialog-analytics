# Dialog Analytics

End-to-end сервис анализа диалогов поддержки: SQL → pandas → LLM-разметка → метрики → FastAPI → дашборд.

Стек: Python, PostgreSQL, Docker, FastAPI, LLM API, Streamlit.

## Статус
- [x] Структура репозитория
- [x] PostgreSQL в Docker Compose
- [x] Схема БД
- [ ] Генерация синтетических данных
- [ ] Загрузка данных в БД
- [ ] SQL-запросы и метрики
- [ ] EDA-ноутбук
- [ ] LLM-разметка
- [ ] FastAPI + Dockerfile
- [ ] ETL и дашборд

## Быстрый старт
cp .env.example .env
docker compose up -d
