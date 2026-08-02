from sqlalchemy import Column, Integer, BigInteger, TIMESTAMP, String, Date
from sqlalchemy.sql import func
from app.core.db import Base

class UserProgression(Base):
    __tablename__ = "user_progression"

    user_id = Column(Integer, primary_key=True)
    total_xp = Column(BigInteger, nullable=False, default=0)
    current_level = Column(Integer, nullable=False, default=1)
    current_streak = Column(Integer, nullable=False, default=0)
    longest_streak = Column(Integer, nullable=False, default=0)
    last_study_date = Column(Date, nullable=True)
    learner_class = Column(String, nullable=True)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
