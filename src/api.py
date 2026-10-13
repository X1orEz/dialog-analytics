"""FastAPI-сервис: разметка диалогов и бизнес-метрики."""
from __future__ import annotations

from contextlib import asynccontextmanager

import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text

from src.db import get_engine
from src.labeling import label_dialogue
from src.metrics import avg_duration_min, dialogues_by_status, retention

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Проверить подключение к БД при старте."""
    try:
        with get_engine().begin() as conn:
            conn.execute(text("SELECT 1"))
        print("DB connection OK")
    except Exception as e:
        print(f"DB connection FAILED: {e}")
    yield
    
app = FastAPI(
    title='Dialog Analytics API',
    version='0.1.0',
    description='Разметка диалогов через LLM и бизнес-метрики.',
    lifespan=lifespan
)


class Message(BaseModel):
    sender: str = Field(..., pattern='^(client|agent)$')
    text : str = Field(..., min_length=1)
    
class LabelRequest(BaseModel):
    messages: list[Message] = Field(..., min_length=1)
    
class LabelResponse(BaseModel):
    topic: str
    sentiment: str
    reason: str    
    
class MetricsResponse(BaseModel):
    total_dialogues: int
    retention: float
    avg_duration_min: float
    by_status: list[dict]
    

@app.get('/health')
def health() -> dict:
    """Проверка, что сервис жив и БД доступна."""
    try:
        with get_engine().begin() as conn:
            conn.execute(text("SELECT 1"))
        return {'status': 'ok', 'db': 'ok'}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f'DB unavailable: {e}')


@app.post('/label', response_model=LabelResponse)
def label(req: LabelRequest) -> LabelResponse:
    """Разметить один диалог через LLM."""
    messages = [m.model_dump() for m in req.messages]
    label = label_dialogue(messages)
    if not label:
        raise HTTPException(status_code=422, detail="Не удалось разметить диалог")
    return LabelResponse(**label)


@app.get('/metrics', response_model=MetricsResponse)
def metrics() -> MetricsResponse:
    """Бизнес-метрики по всем диалогам."""
    engine = get_engine()
    dialogues = pd.read_sql("SELECT * FROM dialogues", engine)
    dialogues['started_at'] = pd.to_datetime(dialogues['started_at'])
    dialogues['ended_at'] = pd.to_datetime(dialogues['ended_at'])
    
    return MetricsResponse(
        total_dialogues=int(len(dialogues)),
        retention=float(retention(dialogues)),
        avg_duration_min=float(avg_duration_min(dialogues)),
        by_status=dialogues_by_status(dialogues).to_dict("records")
    )