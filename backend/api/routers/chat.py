import asyncio
import json
import logging
import time
import uuid

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from api.diagnosis.agent import run_chat_agent
from api.gemini_stt import transcribe_audio_with_gemini


router = APIRouter()
logger = logging.getLogger(__name__)
MAX_INLINE_AUDIO_BYTES = 20 * 1024 * 1024


def _parse_messages(messages: str) -> list[dict]:
    parsed = json.loads(messages)
    if not isinstance(parsed, list):
        raise ValueError("messages must be a JSON array")
    return parsed


async def _transcribe_upload(file: UploadFile) -> str:
    audio_bytes = await file.read()
    if not audio_bytes:
        raise ValueError("빈 음성 파일입니다.")
    if len(audio_bytes) > MAX_INLINE_AUDIO_BYTES:
        raise ValueError("음성 파일은 20MB 이하여야 합니다.")
    return await asyncio.to_thread(
        transcribe_audio_with_gemini,
        audio_bytes,
        file.content_type or "audio/mp4",
    )


async def _create_chat_response(messages: list[dict]) -> dict:
    started_at = time.perf_counter()
    assistant_text = await asyncio.to_thread(run_chat_agent, messages)
    logger.info(
        "voice_chat_complete message_count=%d elapsed_ms=%.1f",
        len(messages),
        (time.perf_counter() - started_at) * 1000,
    )
    updated_messages = [
        *messages,
        {
            "id": f"ai-{uuid.uuid4()}",
            "role": "assistant",
            "content": assistant_text,
        },
    ]
    return {
        "assistant_text": assistant_text,
        "messages": updated_messages,
        "is_diagnosis_ready": "진단" in assistant_text,
    }


@router.post("/chat/transcribe")
async def transcribe_voice(file: UploadFile = File(...)):
    try:
        return {"user_text": await _transcribe_upload(file)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Voice transcription failed")
        raise HTTPException(status_code=500, detail="음성 변환에 실패했습니다.") from exc


@router.post("/chat/respond")
async def respond_to_chat(messages: str = Form("[]")):
    try:
        return await _create_chat_response(_parse_messages(messages))
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="대화 형식이 올바르지 않습니다.") from exc
    except Exception as exc:
        logger.exception("Chat response generation failed")
        raise HTTPException(status_code=500, detail="대화 응답 생성에 실패했습니다.") from exc


@router.post("/chat/voice")
async def chat_voice(file: UploadFile = File(...), messages: str = Form("[]")):
    """Backward-compatible combined endpoint for older app versions."""
    started_at = time.perf_counter()
    try:
        user_text = await _transcribe_upload(file)
        chat_messages = [
            *_parse_messages(messages),
            {
                "id": f"user-{uuid.uuid4()}",
                "role": "user",
                "content": user_text,
            },
        ]
        result = await _create_chat_response(chat_messages)
        logger.info(
            "voice_request_complete elapsed_ms=%.1f",
            (time.perf_counter() - started_at) * 1000,
        )
        return {"user_text": user_text, **result}
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Voice chat processing failed")
        raise HTTPException(status_code=500, detail="음성 채팅 처리에 실패했습니다.") from exc
