from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.core.db import get_db
from app.core.auth import get_current_user_id
from app.core.ranks import get_rank, get_next_rank_threshold, LEARNER_CLASSES
from app.models.progression import UserProgression

router = APIRouter(prefix="/progress", tags=["progress"])


class SetClassRequest(BaseModel):
    learner_class: str


@router.post("/class")
async def set_learner_class(
    req: SetClassRequest,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    if req.learner_class not in LEARNER_CLASSES:
        raise HTTPException(status_code=400, detail=f"Invalid class. Choose from: {LEARNER_CLASSES}")

    result = await db.execute(select(UserProgression).where(UserProgression.user_id == user_id))
    progression = result.scalar_one_or_none()

    if progression is None:
        progression = UserProgression(user_id=user_id, total_xp=0, current_level=1)
        db.add(progression)

    if progression.learner_class is not None:
        raise HTTPException(status_code=400, detail="Class already chosen and cannot be changed.")

    progression.learner_class = req.learner_class
    await db.commit()

    return {"learner_class": progression.learner_class}


@router.get("/classes")
async def list_classes():
    return {"classes": LEARNER_CLASSES}


@router.get("/status")
async def get_status(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    from sqlalchemy import func, and_
    from datetime import datetime, timedelta
    from app.models.skill_unlock import UserSkillUnlock
    from app.models.session import StudySession

    result = await db.execute(select(UserProgression).where(UserProgression.user_id == user_id))
    progression = result.scalar_one_or_none()

    if progression is None:
        progression = UserProgression(user_id=user_id, total_xp=0, current_level=1)

    # Knowledge: skills unlocked
    knowledge_result = await db.execute(
        select(func.count()).select_from(UserSkillUnlock).where(UserSkillUnlock.user_id == user_id)
    )
    knowledge = knowledge_result.scalar() or 0

    # Focus: accuracy across verified sessions (claimed vs verified)
    sessions_result = await db.execute(
        select(StudySession.claimed_seconds, StudySession.verified_seconds)
        .where(StudySession.user_id == user_id, StudySession.status == "verified")
    )
    sessions = sessions_result.all()
    if sessions:
        accuracies = []
        for claimed, verified in sessions:
            if claimed > 0:
                diff_pct = abs(claimed - verified) / claimed * 100
                accuracies.append(max(0, 100 - diff_pct))
        focus = round(sum(accuracies) / len(accuracies)) if accuracies else 100
    else:
        focus = 100  # no sessions yet -- neutral starting value

    # Momentum: verified sessions in the last 7 days
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    momentum_result = await db.execute(
        select(func.count()).select_from(StudySession).where(
            StudySession.user_id == user_id,
            StudySession.status == "verified",
            StudySession.created_at >= seven_days_ago,
        )
    )
    momentum = momentum_result.scalar() or 0

    # Endurance: total verified hours, all-time
    endurance_result = await db.execute(
        select(func.coalesce(func.sum(StudySession.verified_seconds), 0)).where(
            StudySession.user_id == user_id, StudySession.status == "verified"
        )
    )
    total_verified_seconds = endurance_result.scalar() or 0
    endurance_hours = round(total_verified_seconds / 3600, 1)
    endurance_minutes = round(total_verified_seconds / 60)

    rank = get_rank(progression.total_xp)
    next_threshold, next_rank = get_next_rank_threshold(progression.total_xp)

    return {
        "learner_class": progression.learner_class,
        "rank": rank,
        "next_rank": next_rank,
        "xp_to_next_rank": (next_threshold - progression.total_xp) if next_threshold else None,
        "level": progression.current_level,
        "total_xp": progression.total_xp,
        "current_streak": progression.current_streak,
        "longest_streak": progression.longest_streak,
        "stats": {
            "knowledge": knowledge,
            "focus": focus,
            "discipline": progression.current_streak,
            "momentum": momentum,
            "endurance_hours": endurance_hours,
            "endurance_minutes": endurance_minutes,
            "mastery": progression.current_level,
        },
    }


@router.get("/history")
async def get_session_history(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    from app.models.session import StudySession

    result = await db.execute(
        select(StudySession)
        .where(StudySession.user_id == user_id)
        .order_by(StudySession.created_at.desc())
        .limit(50)
    )
    sessions = result.scalars().all()

    return {
        "sessions": [
            {
                "session_id": str(s.session_id),
                "skill_id": s.skill_id,
                "claimed_seconds": s.claimed_seconds,
                "verified_seconds": s.verified_seconds,
                "xp_awarded": s.xp_awarded,
                "status": s.status,
                "created_at": s.created_at.isoformat(),
            }
            for s in sessions
        ]
    }
