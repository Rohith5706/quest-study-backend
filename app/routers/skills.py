from fastapi import APIRouter, Depends
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_db
from app.core.auth import get_current_user_id
from app.models.skill import SkillTree
from app.models.skill_unlock import UserSkillUnlock

router = APIRouter(prefix="/skills", tags=["skills"])

SUBTREE_QUERY = text("""
    WITH RECURSIVE subtree AS (
        SELECT * FROM skill_tree WHERE skill_id = :root_id
        UNION ALL
        SELECT st.* FROM skill_tree st
        JOIN subtree s ON st.parent_id = s.skill_id
    )
    SELECT * FROM subtree;
""")


@router.get("/tree/{root_id}")
async def get_skill_subtree(root_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(SUBTREE_QUERY, {"root_id": root_id})
    rows = result.mappings().all()
    return {"root_id": root_id, "nodes": [dict(row) for row in rows]}


@router.get("/unlocked")
async def get_my_unlocked_skills(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    result = await db.execute(
        select(SkillTree)
        .join(UserSkillUnlock, UserSkillUnlock.skill_id == SkillTree.skill_id)
        .where(UserSkillUnlock.user_id == user_id)
    )
    skills = result.scalars().all()
    return {"unlocked_skills": [{"skill_id": s.skill_id, "name": s.name} for s in skills]}
