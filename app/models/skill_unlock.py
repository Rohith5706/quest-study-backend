from sqlalchemy import Column, Integer, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from app.core.db import Base

class UserSkillUnlock(Base):
    __tablename__ = "user_skill_unlocks"

    user_id = Column(Integer, primary_key=True)
    skill_id = Column(Integer, ForeignKey("skill_tree.skill_id"), primary_key=True)
    unlocked_at = Column(TIMESTAMP(timezone=True), server_default=func.now())