import uuid
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.core.db import get_db
from app.core.auth import get_current_user_id
from app.core.limiter import limiter
from app.services import heartbeat_service, xp_service
from app.models.session import StudySession

router = APIRouter(prefix="/session", tags=["session"])


class StartSessionRequest(BaseModel):
    skill_id: int


class EndSessionRequest(BaseModel):
    session_id: str
    skill_id: int
    claimed_seconds: int


@router.post("/start")
@limiter.limit("5/minute")
async def start_session(
    request: Request,
    req: StartSessionRequest,
    user_id: int = Depends(get_current_user_id),
):
    session_id = await heartbeat_service.start_session(user_id, req.skill_id)
    return {"session_id": session_id}


@router.post("/heartbeat/{session_id}")
async def heartbeat(session_id: str, user_id: int = Depends(get_current_user_id)):
    ok = await heartbeat_service.record_heartbeat(session_id)
    return {"accepted": ok}


@router.post("/end")
async def end_session(
    req: EndSessionRequest,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    verification = await heartbeat_service.end_session(req.session_id, req.claimed_seconds)

    if verification["status"] == "rejected":
        db.add(StudySession(
            session_id=uuid.uuid4(),
            user_id=user_id,
            skill_id=req.skill_id,
            claimed_seconds=req.claimed_seconds,
            verified_seconds=0,
            xp_awarded=0,
            status="rejected",
        ))
        await db.commit()
        return {"xp_awarded": 0, "reason": "session expired / no verification data"}

    seconds_to_credit = verification["verified_seconds"]
    if verification["status"] == "flagged":
        seconds_to_credit = min(seconds_to_credit, 300)

    result = await xp_service.award_xp_and_check_level(
        db,
        user_id=user_id,
        skill_id=req.skill_id,
        verified_seconds=seconds_to_credit,
        claimed_seconds=req.claimed_seconds,
        status=verification["status"],
    )
    result["verification_status"] = verification["status"]
    return result
