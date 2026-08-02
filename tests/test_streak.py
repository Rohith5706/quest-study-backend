import pytest
from datetime import date, timedelta
from app.models.progression import UserProgression
from app.services.xp_service import _update_streak


def test_streak_starts_at_one_on_first_qualifying_session():
    progression = UserProgression(user_id=1, total_xp=0, current_level=1, current_streak=0, longest_streak=0, last_study_date=None)
    _update_streak(progression, verified_seconds=900)
    assert progression.current_streak == 1
    assert progression.longest_streak == 1
    assert progression.last_study_date == date.today()


def test_streak_increments_on_consecutive_day():
    yesterday = date.today() - timedelta(days=1)
    progression = UserProgression(user_id=1, total_xp=0, current_level=1, current_streak=3, longest_streak=5, last_study_date=yesterday)
    _update_streak(progression, verified_seconds=900)
    assert progression.current_streak == 4
    assert progression.longest_streak == 5  # unchanged, 4 < 5


def test_streak_resets_after_gap():
    two_days_ago = date.today() - timedelta(days=2)
    progression = UserProgression(user_id=1, total_xp=0, current_level=1, current_streak=7, longest_streak=7, last_study_date=two_days_ago)
    _update_streak(progression, verified_seconds=900)
    assert progression.current_streak == 1
    assert progression.longest_streak == 7  # untouched, old record stands


def test_short_session_does_not_count():
    progression = UserProgression(user_id=1, total_xp=0, current_level=1, current_streak=2, longest_streak=2, last_study_date=date.today() - timedelta(days=1))
    _update_streak(progression, verified_seconds=300)  # only 5 minutes
    assert progression.current_streak == 2  # unchanged
    assert progression.last_study_date == date.today() - timedelta(days=1)  # unchanged


def test_same_day_session_does_not_double_count():
    progression = UserProgression(user_id=1, total_xp=0, current_level=1, current_streak=1, longest_streak=1, last_study_date=date.today())
    _update_streak(progression, verified_seconds=1000)
    assert progression.current_streak == 1  # unchanged, already counted today
