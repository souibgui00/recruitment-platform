import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy.orm import Session

from shared.database import get_db, SessionLocal
from user_management.dependencies import get_current_user
from user_management.models import User
from matching.models import Match
from job_sourcing.models import JobOffer
from applications.schemas import ApplicationResponse, UserAutoApplySettingsResponse, UserAutoApplySettingsUpdate
from applications.models import ApplicationStatus, Application
from applications.application_service import ApplicationService
from applications.adapters.playwright_application_channel import PlaywrightApplicationChannel

router = APIRouter(prefix="/applications", tags=["applications"])

# Shared Playwright channel adapter
playwright_channel = PlaywrightApplicationChannel()

def _enrich_application(app, db: Session):
    # Retrieve match and job details for nested response enrichment
    match = db.get(Match, app.match_id)
    if match:
        job_offer = db.get(JobOffer, match.job_offer_id)
        app.match_details = {
            "compatibility_score": match.compatibility_score,
            "job_title": job_offer.title if job_offer else "Offre inconnue",
            "company": job_offer.company if job_offer else "Entreprise inconnue",
            "location": job_offer.location if job_offer else "Non précisé",
            "source_url": job_offer.source_url if job_offer else None
        }
    return app

@router.post("/from-match/{match_id}", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
def create_application_from_match(
    match_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crée une candidature à partir d'un match calculé (auto-apply ou manuel).
    """
    app = ApplicationService.process_match(
        match_id=match_id,
        user_id=current_user.id,
        application_channel=playwright_channel,
        db=db
    )
    return _enrich_application(app, db)

@router.get("", response_model=List[ApplicationResponse])
def list_applications(
    status_filter: Optional[ApplicationStatus] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Liste toutes les candidatures de l'utilisateur avec filtre optionnel par statut.
    """
    apps = ApplicationService.get_applications(db, current_user.id, status_filter)
    enriched_apps = [_enrich_application(app, db) for app in apps]
    return enriched_apps



# Background task wrappers to execute Playwright agent with isolated DB sessions
def _run_agent_background(application_id: uuid.UUID, user_id: uuid.UUID):
    db = SessionLocal()
    try:
        ApplicationService.run_agent(
            application_id=application_id,
            user_id=user_id,
            application_channel=playwright_channel,
            db=db
        )
    except Exception as e:
        print(f"Background run_agent failed for app {application_id}: {e}")
    finally:
        db.close()

def _approve_application_background(application_id: uuid.UUID, user_id: uuid.UUID):
    db = SessionLocal()
    try:
        ApplicationService.approve_application(
            application_id=application_id,
            user_id=user_id,
            application_channel=playwright_channel,
            db=db
        )
    except Exception as e:
        print(f"Background approve failed for app {application_id}: {e}")
    finally:
        db.close()

@router.post("/{id}/approve", response_model=ApplicationResponse)
def approve_application(
    id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Approuve manuellement une candidature en attente et déclenche l'agent Playwright en tâche de fond.
    """
    app = db.get(Application, id)
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidature non trouvée")
    if app.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès non autorisé")
    if app.status != ApplicationStatus.PENDING_VALIDATION:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="État de candidature invalide pour approbation")

    # Mark as approved / processing immediately
    app.approve()
    db.commit()
    db.refresh(app)

    background_tasks.add_task(_approve_application_background, app.id, current_user.id)
    return _enrich_application(app, db)

@router.post("/{id}/reject", response_model=ApplicationResponse)
def reject_application(
    id: uuid.UUID,
    reason_payload: Optional[dict] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Rejette manuellement une candidature en attente.
    """
    reason = reason_payload.get("reason") if reason_payload else None
    app = ApplicationService.reject_application(
        application_id=id,
        user_id=current_user.id,
        reason=reason,
        db=db
    )
    return _enrich_application(app, db)

@router.post("/{id}/run-agent", response_model=ApplicationResponse)
def run_agent_for_application(
    id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Exécute l'Agent Web Playwright sur une candidature en tâche de fond.
    """
    app = db.get(Application, id)
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidature non trouvée")
    if app.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès non autorisé")

    # Force temporary status back to APPROVED to signal background processing
    app.status = ApplicationStatus.APPROVED
    db.commit()
    db.refresh(app)

    background_tasks.add_task(_run_agent_background, app.id, current_user.id)
    return _enrich_application(app, db)

@router.get("/settings", response_model=UserAutoApplySettingsResponse)
def get_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère les paramètres auto-apply de l'utilisateur connecté.
    """
    settings = ApplicationService.get_or_create_settings(db, current_user.id)
    return settings

@router.put("/settings", response_model=UserAutoApplySettingsResponse)
def update_settings(
    payload: UserAutoApplySettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Met à jour les paramètres auto-apply de l'utilisateur connecté.
    """
    settings = ApplicationService.update_settings(db, current_user.id, payload.auto_apply_enabled)
    return settings
