from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from api.database import get_db
from api.models import ChatMessage
from api.routers.auth import get_current_user
from api.neo4j import graph

router = APIRouter()


class SendMessageRequest(BaseModel):
    content: str


@router.post("/rooms/{room_id}/send")
def send_message(
    room_id: str,
    request: SendMessageRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    result = graph.query(
        """
        MATCH (u:User {nickname: $nickname})-[:JOINED]->(room:ChatRoom {room_id: $room_id})
        RETURN room
        """,
        {
            "nickname": current_user.nickname,
            "room_id": room_id,
        },
    )

    if not result:
        raise HTTPException(status_code=403, detail="이 채팅방에 참여한 유저가 아닙니다.")

    message = ChatMessage(
        room_id=room_id,
        user_id=current_user.id,
        content=request.content,
    )

    db.add(message)
    db.commit()
    db.refresh(message)

    return {
        "id": message.id,
        "room_id": message.room_id,
        "user_id": message.user_id,
        "content": message.content,
        "created_at": message.created_at,
    }


@router.get("/rooms/{room_id}/messages")
def get_messages(
    room_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    result = graph.query(
        """
        MATCH (u:User {nickname: $nickname})-[:JOINED]->(room:ChatRoom {room_id: $room_id})
        RETURN room
        """,
        {
            "nickname": current_user.nickname,
            "room_id": room_id,
        },
    )

    if not result:
        raise HTTPException(status_code=403, detail="이 채팅방에 참여한 유저가 아닙니다.")

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.room_id == room_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )

    return [
        {
            "id": msg.id,
            "room_id": msg.room_id,
            "user_id": msg.user_id,
            "content": msg.content,
            "created_at": msg.created_at,
        }
        for msg in messages
    ]
