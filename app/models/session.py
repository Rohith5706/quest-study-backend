from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy import TIMESTAMP
from app.core.db import Base

class StudySession(Base):
    __tablename__ = "study_sessions"

    session_id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(Integer, nullable=False)
    skill_id = Column(Integer, ForeignKey("skill_tree.skill_id"), nullable=False)
    claimed_seconds = Column(Integer, nullable=False)
    verified_seconds = Column(Integer, nullable=False)
    xp_awarded = Column(Integer, nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())