import json
import shutil
import traceback
import uuid
from pathlib import Path
from datetime import datetime, timedelta

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer

from api.database import Base, SessionLocal, engine
from api.models import User
from api.schemas import SignupRequest, LoginRequest, DiagnosisRequest
from api.diagnosis_service import analyze_answers, make_recovery_type
from api.agent import run_diagnosis_agent, run_chat_agent
from api.gemini_stt import transcribe_audio_with_gemini

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

app = FastAPI(title="RE:Bloom API")

Base.metadata.create_all(bind=engine)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = "rebloom-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(status_code=401, detail="토큰이 유효하지 않습니다.")

    except JWTError:
        raise HTTPException(status_code=401, detail="토큰이 유효하지 않습니다.")

    user = db.query(User).filter(User.user_id == user_id).first()

    if user is None:
        raise HTTPException(status_code=401, detail="사용자를 찾을 수 없습니다.")

    return user


@app.get("/")
def root():
    return {"message": "RE:Bloom API is running"}

@app.post("/chat/voice")
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

        response = {
            "user_text": user_text,
            "assistant_text": assistant_text,
            "messages"아니 : updated_messages,
            "is_diagnosis_ready": "진단" in assistant_text,
        }

        return response
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="음성 채팅 처리 실패") from e

@app.post("/diagnosis")
async def diagnosis(
    request: dict,
    current_user: User = Depends(get_current_user),
):
    try:
        messages = request.get("messages", [])
        conversation = "\n".join(
            [f"{m['role']}: {m['content']}" for m in messages]
        )

        return run_diagnosis_agent(
            nickname=current_user.nickname,
            conversation=conversation,
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="진단 처리 실패") from e

@app.post("/signup")
def signup(request: SignupRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.user_id == request.user_id).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="이미 존재하는 ID입니다.")

    existing_nickname = db.query(User).filter(User.nickname == request.nickname).first()

    if existing_nickname:
        raise HTTPException(status_code=400, detail="이미 존재하는 nickname입니다.")

    password_hash = pwd_context.hash(request.password)

    new_user = User(
        user_id=request.user_id,
        password_hash=password_hash,
        nickname=request.nickname,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "회원가입 성공",
        "user": {
            "id": new_user.id,
            "user_id": new_user.user_id,
            "nickname": new_user.nickname,
        },
    }


@app.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == request.user_id).first()

    if not user:
        raise HTTPException(status_code=401, detail="존재하지 않는 아이디입니다.")

    is_password_correct = pwd_context.verify(
        request.password,
        user.password_hash
    )

    if not is_password_correct:
        raise HTTPException(status_code=401, detail="비밀번호가 일치하지 않습니다.")

    access_token = create_access_token(
        data={"sub": user.user_id}
    )

    return {
        "message": "로그인 성공",
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "user_id": user.user_id,
            "nickname": user.nickname,
        }
    }

@app.get("/me")
def read_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "user_id": current_user.user_id,
        "nickname": current_user.nickname,
    }

