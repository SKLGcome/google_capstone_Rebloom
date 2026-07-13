from pydantic import BaseModel
from typing import List

class SignupRequest(BaseModel):
    user_id: str
    password: str
    nickname: str


class LoginRequest(BaseModel):
    user_id: str
    password: str

class DiagnosisRequest(BaseModel):
    answers: List[str]

class AnalysisResult(BaseModel):
    energy: int
    direction: int
    action: int
    summary: str


class GraphProfileResult(BaseModel):
    strength_topics: List[str]
    need_topics: List[str]
    goal: str
    experience_tags: List[str]


class RoomMessage(BaseModel):
    content: str
