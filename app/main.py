from contextlib import asynccontextmanager
from datetime import datetime
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.config import get_settings
from app.db import Storage, apply_migrations, get_storage


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Схема создаётся и обновляется при старте: миграции идемпотентны.
    apply_migrations()
    yield


app = FastAPI(title="Guestbook", version=get_settings().app_version, lifespan=lifespan)

StorageDep = Annotated[Storage, Depends(get_storage)]


class EntryIn(BaseModel):
    author: str = Field(min_length=1, max_length=64)
    message: str = Field(min_length=1, max_length=500)


class EntryOut(BaseModel):
    id: int
    author: str
    message: str
    likes: int
    created_at: datetime


@app.get("/health")
def health(storage: StorageDep):
    """Для healthcheck и мониторинга: приложение живо и видит базу."""
    if not storage.ping():
        raise HTTPException(status_code=503, detail="database unavailable")
    return {"status": "ok"}


@app.get("/version")
def version():
    """Какая версия сейчас выкачена. Нужна, чтобы наглядно показать выкат и откат."""
    return {"version": get_settings().app_version}


@app.get("/entries", response_model=list[EntryOut])
def list_entries(storage: StorageDep, limit: int = 50):
    return storage.list_entries(min(max(limit, 1), 200))


@app.post("/entries", response_model=EntryOut, status_code=201)
def add_entry(entry: EntryIn, storage: StorageDep):
    return storage.add_entry(entry.author.strip(), entry.message.strip())
