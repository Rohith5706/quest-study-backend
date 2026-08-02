from sqlalchemy import Column, Integer, String, ForeignKey
from app.core.db import Base

class SkillTree(Base):
    __tablename__ = "skill_tree"

    skill_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    parent_id = Column(Integer, ForeignKey("skill_tree.skill_id"))
    xp_required = Column(Integer, nullable=False, default=0)
    subject = Column(String, nullable=False)