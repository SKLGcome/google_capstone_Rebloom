from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI

from api.database import Base, engine

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

from api.routers import auth, chat, diagnosis,chat_rooms  # noqa: E402

app = FastAPI(title="RE:Bloom API")

Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {"message": "RE:Bloom API is running"}


app.include_router(auth.router)
app.include_router(diagnosis.router)
app.include_router(chat.router)
app.include_router(chat_rooms.router)