import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, UploadFile, Depends, HTTPException
from sqlalchemy.orm import Session

from shared.database import get_db
from cv_management.models import CV
from cv_management.schemas import CVResponse
from cv_management.text_extraction import extract_text_from_pdf
from cv_management.llm_extraction import test_llm_connection


router = APIRouter(prefix="/cv", tags=["cv"])

UPLOAD_DIR = Path("uploaded_cvs")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/upload", response_model=CVResponse)
def upload_cv(file: UploadFile, db: Session = Depends(get_db)):
    file_path = UPLOAD_DIR / f"{uuid.uuid4()}_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    cv = CV(
        user_id=uuid.uuid4(),
        raw_file_url=str(file_path),
        language="FR",
        status="UPLOADED",
    )
    db.add(cv)
    db.commit()
    db.refresh(cv)

    return cv



@router.get("/{cv_id}/extract-preview")
def extract_preview(cv_id: uuid.UUID, db: Session = Depends(get_db)):
    cv = db.get(CV, cv_id)
    if not cv:
        raise HTTPException(status_code=404, detail="CV non trouvé")

    text = extract_text_from_pdf(cv.raw_file_url)
    return {"text_preview": text[:500]}

@router.get("/test-llm")
def test_llm():
    return {"response": test_llm_connection()}