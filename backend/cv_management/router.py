import shutil
import uuid
from pathlib import Path
from typing import List

from fastapi import APIRouter, UploadFile, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel as PydanticBaseModel

class UpdatePersonalInfoRequest(PydanticBaseModel):
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    salary_expectation: str | None = None

from shared.database import get_db
from cv_management.models import CV, CVStatus, PersonalInfo, Experience, Education, CVSkill, Skill
from cv_management.schemas import CVResponse
from cv_management.parsing_service import parse_cv
from user_management.dependencies import get_current_user
from user_management.models import User

from cv_management.adapters.pdf_text_extractor import PdfTextExtractor
from cv_management.adapters.groq_llm_extractor import GroqLLMExtractor
from cv_management.adapters.e5_embedding_provider import E5EmbeddingProvider

router = APIRouter(prefix="/cv", tags=["cv"])

UPLOAD_DIR = Path("uploaded_cvs")
UPLOAD_DIR.mkdir(exist_ok=True)

# Instantiate adapters as singletons at startup
text_extractor = PdfTextExtractor()
llm_extractor = GroqLLMExtractor()
embedding_provider = E5EmbeddingProvider()


def _enrich_cv(cv: CV, db: Session) -> CV:
    """Load all related data for a CV so the response schema can serialize it."""
    cv.personal_info = db.query(PersonalInfo).filter_by(cv_id=cv.id).first()
    cv.experiences = db.query(Experience).filter_by(cv_id=cv.id).all()
    cv.educations = db.query(Education).filter_by(cv_id=cv.id).all()

    # Load skills via join
    cv_skills = db.query(CVSkill).filter_by(cv_id=cv.id).all()
    skill_ids = [cs.skill_id for cs in cv_skills]
    cv.skills = db.query(Skill).filter(Skill.id.in_(skill_ids)).all() if skill_ids else []

    return cv


@router.get("", response_model=List[CVResponse])
@router.get("/", response_model=List[CVResponse])
def list_cvs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Liste tous les CVs de l'utilisateur connecté avec leurs données parsées."""
    cvs = db.query(CV).filter(CV.user_id == current_user.id).order_by(CV.created_at.desc()).all()
    return [_enrich_cv(cv, db) for cv in cvs]


@router.get("/{cv_id}", response_model=CVResponse)
def get_cv(
    cv_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupère un CV par son ID avec toutes les données parsées."""
    cv = db.get(CV, cv_id)
    if not cv:
        raise HTTPException(status_code=404, detail="CV non trouvé")
    if cv.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    return _enrich_cv(cv, db)


@router.post("/upload", response_model=CVResponse)
def upload_cv(
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload et parse un fichier PDF CV pour l'utilisateur connecté."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Seuls les fichiers PDF sont supportés pour l'instant.")

    file_path = UPLOAD_DIR / f"{uuid.uuid4()}_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    cv = CV(
        user_id=current_user.id,
        filename=file.filename,
        raw_file_url=str(file_path),
        language="FR",
        status=CVStatus.UPLOADED,
    )
    db.add(cv)
    db.commit()
    db.refresh(cv)

    # Parse automatiquement le CV après upload
    parse_cv(cv, db, text_extractor, llm_extractor, embedding_provider)
    db.refresh(cv)

    return _enrich_cv(cv, db)


@router.put("/{cv_id}/personal-info")
def update_personal_info(
    cv_id: uuid.UUID,
    payload: UpdatePersonalInfoRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    cv = db.get(CV, cv_id)
    if not cv:
        raise HTTPException(status_code=404, detail="CV non trouvé")
    if cv.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    personal_info = db.query(PersonalInfo).filter_by(cv_id=cv_id).first()
    if not personal_info:
        raise HTTPException(status_code=404, detail="Informations personnelles non trouvées")
    
    if payload.full_name is not None:
        personal_info.full_name = payload.full_name
    if payload.email is not None:
        personal_info.email = payload.email
    if payload.phone is not None:
        personal_info.phone = payload.phone
    if payload.location is not None:
        personal_info.location = payload.location
    if payload.linkedin_url is not None:
        personal_info.linkedin_url = payload.linkedin_url
    if payload.github_url is not None:
        personal_info.github_url = payload.github_url
    if payload.salary_expectation is not None:
        personal_info.salary_expectation = payload.salary_expectation
    
    db.commit()
    db.refresh(personal_info)
    return {
        "status": "updated",
        "full_name": personal_info.full_name,
        "email": personal_info.email,
        "phone": personal_info.phone,
        "location": personal_info.location,
        "linkedin_url": personal_info.linkedin_url,
        "github_url": personal_info.github_url,
        "salary_expectation": personal_info.salary_expectation
    }


@router.delete("/{cv_id}")
def delete_cv(
    cv_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Supprime un CV de l'utilisateur connecté ainsi que toutes ses données associées."""
    cv = db.get(CV, cv_id)
    if not cv:
        raise HTTPException(status_code=404, detail="CV non trouvé")
    if cv.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    # Imports for cascading delete
    from cv_management.models import Experience, Education, Certification, CVSkill, PersonalInfo, CVEmbedding
    from matching.models import Match

    # Manual cascade delete
    db.query(Match).filter_by(cv_id=cv_id).delete()
    db.query(Experience).filter_by(cv_id=cv_id).delete()
    db.query(Education).filter_by(cv_id=cv_id).delete()
    db.query(Certification).filter_by(cv_id=cv_id).delete()
    db.query(CVSkill).filter_by(cv_id=cv_id).delete()
    db.query(PersonalInfo).filter_by(cv_id=cv_id).delete()
    db.query(CVEmbedding).filter_by(cv_id=cv_id).delete()
    
    db.delete(cv)
    db.commit()
    return {"status": "deleted", "cv_id": str(cv_id)}