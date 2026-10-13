# Dialog Analytics

End-to-end сервис анализа диалогов поддержки: SQL → pandas → LLM-разметка → метрики → FastAPI → дашборд.

Стек: **Python 3.12, PostgreSQL, Docker, FastAPI, Ollama (LLM), Streamlit**.

## Что делает

- Загружает синтетические диалоги клиентов в Postgres.
- Размечает диалоги через локальную LLM (тема, тональность, причина обращения).
- Считает бизнес-метрики: retention, средняя длительность, распределения по каналам и статусам.
- Обучает модель предсказания эскалации (ROC-AUC ≈ 0.78).
- Отдаёт разметку и метрики по HTTP через FastAPI.
- Показывает результаты в Streamlit-дашборде.

## Архитектура

```
CSV → PostgreSQL → pandas → LLM-разметка → метрики → FastAPI → Streamlit
                        ↓
                    Ollama (llama3.2:3b)
```

Сервисы поднимаются через `docker compose`:

| Сервис     | Порт  | Назначение                    |
|------------|-------|-------------------------------|
| `postgres` | 5432  | База данных                   |
| `ollama`   | 11434 | Локальный LLM-сервер          |
| `api`      | 8000  | FastAPI-сервис                |
| `dashboard`| 8501  | Streamlit-дашборд (День 6)    |

## Быстрый старт

1. Клонируй репозиторий:
   ```bash
   git clone https://github.com/X1orEz/dialog-analytics.git
   cd dialog-analytics
   ```

2. Скопируй переменные окружения:
   ```bash
   cp .env.example .env
   ```

3. Подними сервисы:
   ```bash
   docker compose up -d
   ```

4. Скачай LLM-модель (один раз, ~2 ГБ):
   ```bash
   docker compose exec ollama ollama pull llama3.2:3b
   ```

5. Сгенерируй и загрузи данные:
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   pip install -e .
   python -m src.generate_data
   python -m src.db
   ```

6. Размечай диалоги через LLM:
   ```bash
   python -m src.labeling
   ```

7. Открой API:
   - Swagger UI: http://localhost:8000/docs
   - Health: http://localhost:8000/health
   - Дашборд: http://localhost:8501

## API

| Метод | Эндпоинт   | Назначение                          |
|-------|------------|-------------------------------------|
| GET   | `/health`  | Проверка состояния сервиса и БД     |
| POST  | `/label`   | Разметить один диалог через LLM     |
| GET   | `/metrics` | Бизнес-метрики по всем диалогам     |

Пример разметки:

```bash
curl -X POST http://localhost:8000/label \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"sender": "client", "text": "С меня списали деньги дважды"}]}'
```

Ответ:

```json
{"topic": "billing", "sentiment": "negative", "reason": "двойное списание"}
```

## Структура проекта

```
dialog-analytics/
├── sql/                # Схема БД и бизнес-запросы
├── notebooks/          # EDA и ML-исследования
├── src/
│   ├── generate_data.py    # генерация синтетики
│   ├── db.py               # загрузка в Postgres
│   ├── labeling.py         # LLM-разметка
│   ├── metrics.py          # бизнес-метрики
│   ├── stats.py            # статистические тесты
│   ├── evaluate.py         # ML-метрики
│   ├── evaluate_labeling.py # оценка качества разметки
│   ├── llm_client.py       # клиент для Ollama
│   └── api.py              # FastAPI-сервис
├── reports/            # отчёты по метрикам и разметке
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## Что сделано

- [x] Структура репозитория и Git
- [x] PostgreSQL в Docker Compose
- [x] Схема БД (`clients`, `dialogues`, `messages`, `labels`)
- [x] Генерация синтетических данных (200 клиентов, 800 диалогов)
- [x] SQL-запросы с CTE, оконными функциями, JOIN
- [x] EDA-ноутбук с визуализациями
- [x] Статистика: t-test, chi-square, bootstrap
- [x] Модель предсказания эскалации (ROC-AUC ≈ 0.78)
- [x] LLM-разметка диалогов через Ollama (`llama3.2:3b`)
- [x] Оценка качества разметки (Cohen's kappa)
- [x] FastAPI-сервис с `/label`, `/metrics`, `/health`
- [x] Docker: API + Postgres + Ollama
- [x] Streamlit-дашборд с фильтрами
- [x] ETL-пайплайн (`src/etl.py`)

## Метрики

- **Разметка (LLM vs ручной эталон, n=50):** Cohen's kappa = 1.0 на синтетических данных.
- **Модель эскалации:** ROC-AUC = 0.776, PR-AUC = 0.413.

Подробности: [`reports/stats_report.md`](reports/stats_report.md), [`reports/labeling_quality.md`](reports/labeling_quality.md).

## Ограничения

- Данные синтетические — метрики отражают заложенные в генератор закономерности, а не реальные бизнес-процессы.
- LLM работает локально в контейнере (CPU), для больших моделей нужен GPU.
- Разметка `reason` иногда содержит артефакты (не-русские символы) — это ограничение модели 3B.
