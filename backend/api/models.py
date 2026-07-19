from datetime import datetime

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)

from api.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    nickname = Column(String, unique=True, index=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

class Diagnosis(Base):
    __tablename__ = "diagnoses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    recovery_type = Column(String)
    summary = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(String, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class DailyMission(Base):
    __tablename__ = "daily_missions"

    id = Column(Integer, primary_key=True, index=True)

    mission_name = Column(String, nullable=False)
    mission_date = Column(Date, nullable=False, index=True)
    recovery_type = Column(String, nullable=False, index=True)
    mission_content = Column(Text, nullable=False)

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "recovery_type",
            "mission_date",
            name="uq_daily_mission_type_date",
        ),
    )


class MissionCompletion(Base):
    __tablename__ = "mission_completions"

    id = Column(Integer, primary_key=True, index=True)
    mission_id = Column(
        Integer,
        ForeignKey("daily_missions.id"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    completed_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "mission_id",
            "user_id",
            name="uq_mission_completion_user",
        ),
    )
