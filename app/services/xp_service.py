import uuid
from datetime import date, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.progression import UserProgression
from app.models.skill import SkillTree
from app.models.session import StudySession
from app.models.skill_unlock import UserSkillUnlock

XP_PER_SECOND = 1
STREAK_THRESHOLD_SECONDS = 900


def level_xp_threshold(level: int) -> int:
    return 100 * level * level


def _update_streak(progression: UserProgression, verified_seconds: int) -> None:
    """Mutates progression's streak fields in place based on today's session."""
    if verified_seconds < STREAK_THRESHOLD_SECONDS:
        return  # session too short to count toward a streak

    today = date.today()

    if progression.last_study_date == today:
        return  # already counted today, no double-counting

    if progression.last_study_date == today - timedelta(days=1):
        progression.current_streak += 1  # continued from yesterday
    else:
        progression.current_streak = 1  # gap in days, or very first qualifying session

    progression.longest_streak = max(progression.longest_streak, progression.current_streak)
    progression.last_study_date = today


async def award_xp_and_check_level(
    db: AsyncSession,
    user_id: int,
    skill_id: int,
    verified_seconds: int,
    claimed_seconds: int,
    status: str,
) -> dict:
    xp_gained = verified_seconds * XP_PER_SECOND

    async with db.begin():
        result = await db.execute(
            select(UserProgression)
            .where(UserProgression.user_id == user_id)
            .with_for_update()
        )
        progression = result.scalar_one_or_none()

        if progression is None:
            progression = UserProgression(user_id=user_id, total_xp=0, current_level=1)
            db.add(progression)
            await db.flush()

        progression.total_xp += xp_gained
        _update_streak(progression, verified_seconds)

        leveled_up = False
        while progression.total_xp >= level_xp_threshold(progression.current_level):
            progression.current_level += 1
            leveled_up = True

        unlocked_skills = []
        if leveled_up:
            result = await db.execute(
                select(SkillTree).where(
                    SkillTree.parent_id == skill_id,
                    SkillTree.xp_required <= progression.total_xp,
                )
            )
            candidates = result.scalars().all()

            already_unlocked_result = await db.execute(
                select(UserSkillUnlock.skill_id).where(UserSkillUnlock.user_id == user_id)
            )
            already_unlocked_ids = {row for row in already_unlocked_result.scalars().all()}

            for skill in candidates:
                if skill.skill_id not in already_unlocked_ids:
                    db.add(UserSkillUnlock(user_id=user_id, skill_id=skill.skill_id))
                    unlocked_skills.append(skill.skill_id)

        db.add(StudySession(
            session_id=uuid.uuid4(),
            user_id=user_id,
            skill_id=skill_id,
            claimed_seconds=claimed_seconds,
            verified_seconds=verified_seconds,
            xp_awarded=xp_gained,
            status=status,
        ))

        return {
            "xp_gained": xp_gained,
            "total_xp": progression.total_xp,
            "current_level": progression.current_level,
            "leveled_up": leveled_up,
            "unlocked_skills": unlocked_skills,
            "current_streak": progression.current_streak,
            "longest_streak": progression.longest_streak,
        }
