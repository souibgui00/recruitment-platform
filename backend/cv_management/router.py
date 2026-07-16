import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, UploadFile, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from shared.database import get_db
from cv_management.models import CV, CVStatus
from cv_management.schemas import CVResponse
from cv_management.parsing_service import parse_cv

from cv_management.adapters.pdf_text_extractor import PdfTextExtractor
from cv_management.adapters.groq_llm_extractor import GroqLLMExtractor
from cv_management.adapters.e5_embedding_provider import E5EmbeddingProvider

router = APIRouter(prefix="/cv", tags=["cv"])

UPLOAD_DIR = Path("uploaded_cvs")
UPLOAD_DIR.mkdir(exist_ok=True)

FIXED_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")

# Instantiate adapters as singletons at startup
text_extractor = PdfTextExtractor()
llm_extractor = GroqLLMExtractor()
embedding_provider = E5EmbeddingProvider()


@router.post("/upload", response_model=CVResponse)
def upload_cv(file: UploadFile, db: Session = Depends(get_db)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Seuls les fichiers PDF sont supportés pour l'instant.")

    file_path = UPLOAD_DIR / f"{uuid.uuid4()}_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    cv = CV(
        user_id=FIXED_USER_ID,
        raw_file_url=str(file_path),
        language="FR",
        status=CVStatus.UPLOADED,
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

    text = text_extractor.extract_text(cv.raw_file_url)
    return {"text_preview": text[:500]}


@router.get("/{cv_id}/extract-structured")
def extract_structured(cv_id: uuid.UUID, db: Session = Depends(get_db)):
    cv = db.get(CV, cv_id)
    if not cv:
        raise HTTPException(status_code=404, detail="CV non trouvé")

    text = text_extractor.extract_text(cv.raw_file_url)
    parsed_data = llm_extractor.extract_structured_data(text)
    return parsed_data


@router.post("/{cv_id}/parse")
def parse_cv_endpoint(cv_id: uuid.UUID, db: Session = Depends(get_db)):
    cv = db.get(CV, cv_id)
    if not cv:
        raise HTTPException(status_code=404, detail="CV non trouvé")

    parse_cv(cv, db, text_extractor, llm_extractor, embedding_provider)
    return {"status": "success", "cv_id": str(cv.id)}