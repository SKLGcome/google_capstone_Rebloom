import os
import mimetypes
from google import genai

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def transcribe_audio_with_gemini(file_path: str) -> str:
    print("=== Gemini STT 시작 ===")
    print("file_path:", file_path)
    print("exists:", os.path.exists(file_path))
    print("size:", os.path.getsize(file_path))

    mime_type, _ = mimetypes.guess_type(file_path)
    print("guessed mime_type:", mime_type)

    audio_file = client.files.upload(
        file=file_path,
        config={"mime_type": mime_type or "audio/mp4"}
    )

    print("uploaded file:", audio_file)
    print("uploaded name:", getattr(audio_file, "name", None))
    print("uploaded mime:", getattr(audio_file, "mime_type", None))
    print("uploaded state:", getattr(audio_file, "state", None))

    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=[
            audio_file,
            "이 음성 파일의 한국어 발화를 텍스트로 정확히 변환해줘. 설명 없이 변환된 문장만 출력해.",
        ],
    )

    print("Gemini raw response:", response)
    print("Gemini text:", response.text)

    return response.text.strip()