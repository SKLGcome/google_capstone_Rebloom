import json
import shutil
import traceback
import uuid
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from api.agent import run_chat_agent
from api.gemini_stt import transcribe_audio_with_gemini

router = APIRouter()


@router.post("/chat/voice")
async def chat_voice(
    file: UploadFile = File(...),
    messages: str = Form("[]"),
):
    try:
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        file_path = upload_dir / f"{uuid.uuid4()}_{file.filename}"

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        user_text = transcribe_audio_with_gemini(str(file_path))
        prev_messages = json.loads(messages)
        chat_messages = [
            *prev_messages,
            {
                "id": f"user-{uuid.uuid4()}",
                "role": "user",
                "content": user_text,
            },
        ]
        assistant_text = run_chat_agent(chat_messages)
        updated_messages = [
            *chat_messages,
            {
                "id": f"ai-{uuid.uuid4()}",
                "role": "assistant",
                "content": assistant_text,
            },
        ]

        return {
            "user_text": user_text,
            "assistant_text": assistant_text,
            "messages": updated_messages,
            "is_diagnosis_ready": "진단" in assistant_text,
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="음성 채팅 처리 실패") from e
