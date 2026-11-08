from datetime import UTC, datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api import _job_out, _profile_out, create_and_enqueue
from app.catalog import normalize_skill
from app.database import get_db
from app.models import Profile, ResumeAnalysis, User
from app.resume_analysis import MAX_BYTES, ResumeError, extract_text
from app.schemas import ProfileResponse, ResumeResponse, ResumeUploadResponse
from app.security import get_current_user

router = APIRouter(prefix="/api/v1/resume")


def _resume_out(row: ResumeAnalysis) -> ResumeResponse:
    return ResumeResponse(
        id=row.id,
        filename=row.filename,
        status=row.status,
        provider=row.provider,
        notice=row.notice,
        error=row.error,
        created_at=row.created_at,
        analysis=row.analysis,
        comparison=row.comparison,
    )


def _owned(db: Session, user: User, resume_id: str) -> ResumeAnalysis:
    row = db.get(ResumeAnalysis, resume_id)
    if row is None or row.user_id != user.id:
        raise HTTPException(status_code=404, detail="Resume analysis not found")
    return row


@router.post("/analyze", response_model=ResumeUploadResponse, status_code=202)
def analyze_resume(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResumeUploadResponse:
    # Read at most one byte past the limit so an oversized upload is rejected without loading it all.
    data = file.file.read(MAX_BYTES + 1)
    try:
        text = extract_text(file.filename or "", file.content_type, data)
    except ResumeError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    row = ResumeAnalysis(
        user_id=user.id,
        filename=(file.filename or "resume")[:255],
        status="queued",
        source_text=text,
        created_at=datetime.now(UTC),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    try:
        job = create_and_enqueue(db, user.id, "resume", {"resume_id": row.id})
    except HTTPException:
        row.status = "failed"
        row.error = "The job queue is unavailable."
        row.source_text = None
        db.commit()
        raise
    return ResumeUploadResponse(resume_id=row.id, job=_job_out(job))


@router.get("/latest", response_model=ResumeResponse | None)
def latest_resume(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ResumeResponse | None:
    row = (
        db.query(ResumeAnalysis)
        .filter(ResumeAnalysis.user_id == user.id)
        .order_by(ResumeAnalysis.created_at.desc())
        .first()
    )
    return _resume_out(row) if row else None


@router.delete("/{resume_id}", status_code=204)
def delete_resume(resume_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    db.delete(_owned(db, user, resume_id))
    db.commit()


@router.post("/{resume_id}/apply-to-profile", response_model=ProfileResponse)
def apply_to_profile(
    resume_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> ProfileResponse:
    """Add skills found in the resume that the profile does not list yet, with conservative starting levels."""
    row = _owned(db, user, resume_id)
    if row.status != "completed" or not row.analysis:
        raise HTTPException(status_code=409, detail="The resume analysis is not finished yet")
    profile = db.query(Profile).filter(Profile.user_id == user.id).first()
    if profile is None:
        raise HTTPException(status_code=409, detail="Create your career profile first")
    skills = list(profile.skills or [])
    known = {normalize_skill(str(item.get("name", ""))) for item in skills}
    for skill in row.analysis.get("skills", []):
        level = {"demonstrated": 2, "listed": 1}.get(skill.get("evidence_level"))
        key = normalize_skill(str(skill.get("name", "")))
        if level is None or not key or key in known or len(skills) >= 30:
            continue
        known.add(key)
        skills.append({"name": str(skill["name"])[:60], "proficiency": level})
    profile.skills = skills
    profile.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(profile)
    return _profile_out(profile)
