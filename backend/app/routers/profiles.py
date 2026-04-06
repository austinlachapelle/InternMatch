from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import shutil

from fastapi import APIRouter, Depends, File, Form, UploadFile

from ..database import STORAGE_DIR, get_connection
from ..dependencies import get_current_user
from ..services.metro import METRO_AREAS


router = APIRouter(tags=["profiles"])
UPLOAD_DIR = STORAGE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.get("/profiles")
def list_profiles(current_user: dict[str, object] = Depends(get_current_user)) -> dict[str, object]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, target_role, gpa, metro_slug, metro_name, resume_url, transcript_url, created_at
            FROM profiles
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (current_user["id"],),
        ).fetchall()

    return {
        "profiles": [
            {
                "id": row["id"],
                "targetRole": row["target_role"],
                "gpa": row["gpa"],
                "metroSlug": row["metro_slug"],
                "metroName": row["metro_name"],
                "resumeUrl": row["resume_url"],
                "transcriptUrl": row["transcript_url"],
                "createdAt": row["created_at"],
            }
            for row in rows
        ]
    }


@router.post("/profiles")
async def create_profile(
    target_role: str = Form(...),
    gpa: float = Form(...),
    metro_slug: str = Form(...),
    resume: UploadFile = File(...),
    transcript: UploadFile = File(...),
    current_user: dict[str, object] = Depends(get_current_user),
) -> dict[str, object]:
    metro_name = METRO_AREAS.get(metro_slug)
    profile_id = str(uuid4())
    resume_url = _save_upload(profile_id, "resume", resume)
    transcript_url = _save_upload(profile_id, "transcript", transcript)

    created_at = datetime.now(timezone.utc).isoformat()
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO profiles (user_id, target_role, gpa, metro_slug, metro_name, resume_url, transcript_url, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                current_user["id"],
                target_role,
                gpa,
                metro_slug,
                metro_name.name if metro_name else metro_slug,
                resume_url,
                transcript_url,
                created_at,
            ),
        )
        connection.commit()

    return {
        "profile": {
            "id": cursor.lastrowid,
            "targetRole": target_role,
            "gpa": gpa,
            "metroSlug": metro_slug,
            "metroName": metro_name.name if metro_name else metro_slug,
            "resumeUrl": resume_url,
            "transcriptUrl": transcript_url,
            "createdAt": created_at,
        }
    }


def _save_upload(profile_id: str, label: str, upload: UploadFile) -> str:
    suffix = Path(upload.filename or "").suffix or ".pdf"
    filename = f"{profile_id}-{label}{suffix}"
    destination = UPLOAD_DIR / filename
    with destination.open("wb") as output:
        shutil.copyfileobj(upload.file, output)
    return f"/uploads/{filename}"
