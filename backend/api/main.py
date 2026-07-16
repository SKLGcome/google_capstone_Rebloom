import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI

from api.database import Base, engine

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

from api.routers import auth, chat, chat_rooms, diagnosis, missions  # noqa: E402
from api.mission_scheduler import run_daily_mission_scheduler  # noqa: E402
from api.rag.indexer import ensure_mission_index  # noqa: E402


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    index_rebuilt = await asyncio.to_thread(ensure_mission_index)
    if index_rebuilt:
        logger.info("Mission index rebuilt from source documents")
    else:
        logger.info("Mission index is up to date")

    scheduler_task = asyncio.create_task(run_daily_mission_scheduler())
    try:
        yield
    finally:
        scheduler_task.cancel()
        try:
            await scheduler_task
        except asyncio.CancelledError:
            pass


app = FastAPI(title="RE:Bloom API", lifespan=lifespan)

Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {"message": "RE:Bloom API is running"}


app.include_router(auth.router)
app.include_router(diagnosis.router)
app.include_router(chat.router)
app.include_router(chat_rooms.router)
app.include_router(missions.router)
