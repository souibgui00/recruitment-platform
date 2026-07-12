import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, UploadFile, Depends
from sqlalchemy.orm import Session

from shared.database import get_db
from cv_management.models import CV
from cv_management.schemas import CVResponse

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