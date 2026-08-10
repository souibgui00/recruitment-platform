import uuid
from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from cv_management.models import CV, PersonalInfo, Experience, CVSkill, Skill
from job_sourcing.models import JobOffer
from matching.models import Match, MatchingConfig
from matching.matching_service import MatchingService
from applications.models import Application, UserAutoApplySettings, ApplicationMode, ApplicationStatus
from applications.ports.application_channel import IApplicationChannel
from notifications.models import NotificationType
from notifications.services import NotificationService


def _fetch_cv_enrichment(db: Session, cv_id: uuid.UUID):
    """
    Fetches all enrichment data for a CV to build a rich application email:
    - personal_info: PersonalInfo object
    - experiences: list of Experience objects (newest first)
    - skills: list of skill names
    """
    personal_info = db.query(PersonalInfo).filter_by(cv_id=cv_id).first()
    experiences = (
        db.query(Experience)
        .filter_by(cv_id=cv_id)
        .order_by(Experience.start_date.desc())
        .all()
    )
    # Fetch skill names via join
    cv_skills = db.query(CVSkill).filter_by(cv_id=cv_id).all()
    skill_names = []
    for cs in cv_skills:
        skill = db.get(Skill, cs.skill_id)
        if skill:
            skill_names.append(skill.canonical_name)

    return personal_info, experiences, skill_names


class ApplicationService:
    @staticmethod
    def get_or_create_settings(db: Session, user_id: uuid.UUID) -> UserAutoApplySettings:
        settings = db.query(UserAutoApplySettings).filter_by(user_id=user_id).first()
        if not settings:
            settings = UserAutoApplySettings(user_id=user_id, auto_apply_enabled=False)
            db.add(settings)
            db.commit()
            db.refresh(settings)
        return settings

    @staticmethod
    def update_settings(db: Session, user_id: uuid.UUID, auto_apply_enabled: bool) -> UserAutoApplySettings:
        settings = ApplicationService.get_or_create_settings(db, user_id)
        settings.auto_apply_enabled = auto_apply_enabled
        db.commit()
        db.refresh(settings)
        return settings

    @staticmethod
    def process_match(
        match_id: uuid.UUID,
        user_id: uuid.UUID,
        application_channel: IApplicationChannel,
        db: Session
    ) -> Application:
        # 1. Fetch match and verify existence
        match = db.get(Match, match_id)
        if not match:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match non trouvé")

        # 2. Security Check: Ownership verification via CV
        cv = db.get(CV, match.cv_id)
        if not cv or cv.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accès non autorisé : ce match ne vous appartient pas."
            )

        # 3. Check for duplicates
        existing_app = db.query(Application).filter_by(match_id=match_id).first()
        if existing_app:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Une candidature existe déjà pour ce match."
            )

        # 4. Fetch settings & matching config
        auto_apply_settings = ApplicationService.get_or_create_settings(db, user_id)
        matching_config = MatchingService.get_or_create_config(user_id, db)
        job_offer = db.get(JobOffer, match.job_offer_id)

        # 5. Decide mode
        is_above_threshold = match.compatibility_score >= matching_config.threshold
        is_auto_enabled = auto_apply_settings.auto_apply_enabled

        if is_auto_enabled and is_above_threshold:
            mode = ApplicationMode.FULL_AUTO
            initial_status = ApplicationStatus.PENDING_VALIDATION
        else:
            mode = ApplicationMode.MANUAL_VALIDATION
            initial_status = ApplicationStatus.PENDING_VALIDATION

        # Create Application record
        application = Application(
            match_id=match_id,
            user_id=user_id,
            mode=mode,
            status=initial_status
        )
        db.add(application)
        db.flush()  # get UUID assigned

        if mode == ApplicationMode.FULL_AUTO:
            # Fetch all enrichment data for rich email
            personal_info, experiences, skill_names = _fetch_cv_enrichment(db, cv.id)
            candidate_email = personal_info.email if personal_info else None

            result = application_channel.submit(
                application, cv, job_offer,
                candidate_email=candidate_email,
                match=match,
                personal_info=personal_info,
                experiences=experiences,
                skills=skill_names
            )
            application.cover_letter = result.get("cover_letter")
            application.execution_logs = result.get("execution_logs")
            application.screenshots = result.get("screenshots")

            if result.get("success"):
                status_returned = result.get("status", "SENT")
                if status_returned == "MANUAL_REQUIRED":
                    reason = result.get("error_message") or "Intervention humaine requise (CAPTCHA ou Login)"
                    application.mark_as_manual_required(reason)
                    NotificationService.create_notification(
                        db=db,
                        user_id=user_id,
                        type=NotificationType.APPLICATION_FAILED,
                        message=f"Action requise pour {job_offer.title} chez {job_offer.company} : {reason}.",
                        related_application_id=application.id
                    )
                else:
                    application.mark_as_sent()
                    NotificationService.create_notification(
                        db=db,
                        user_id=user_id,
                        type=NotificationType.APPLICATION_SENT,
                        message=f"Candidature traitée avec succès pour {job_offer.title} chez {job_offer.company}.",
                        related_application_id=application.id
                    )
            else:
                reason = result.get("error_message") or "Erreur d'exécution de l'agent web"
                application.mark_as_failed(reason)
                NotificationService.create_notification(
                    db=db,
                    user_id=user_id,
                    type=NotificationType.APPLICATION_FAILED,
                    message=f"Échec de l'envoi automatique pour {job_offer.title} chez {job_offer.company} : {reason}.",
                    related_application_id=application.id
                )

        db.commit()
        db.refresh(application)
        return application

    @staticmethod
    def approve_application(
        application_id: uuid.UUID,
        user_id: uuid.UUID,
        application_channel: IApplicationChannel,
        db: Session
    ) -> Application:
        # 1. Fetch application
        application = db.get(Application, application_id)
        if not application:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidature non trouvée")

        # 2. Check ownership
        if application.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accès non autorisé : cette candidature appartient à un autre utilisateur."
            )

        # 3. Check transition
        if application.status != ApplicationStatus.PENDING_VALIDATION:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Impossible d'approuver une candidature dans l'état : {application.status}."
            )

        # 4. State transition
        application.approve()

        # Fetch resources
        match = db.get(Match, application.match_id)
        cv = db.get(CV, match.cv_id)
        job_offer = db.get(JobOffer, match.job_offer_id)

        # Fetch all enrichment data for rich email
        personal_info, experiences, skill_names = _fetch_cv_enrichment(db, cv.id)
        candidate_email = personal_info.email if personal_info else None

        # 5. Submit with full enrichment
        result = application_channel.submit(
            application, cv, job_offer,
            candidate_email=candidate_email,
            match=match,
            personal_info=personal_info,
            experiences=experiences,
            skills=skill_names
        )
        application.cover_letter = result.get("cover_letter")
        application.execution_logs = result.get("execution_logs")
        application.screenshots = result.get("screenshots")

        if result.get("success"):
            status_returned = result.get("status", "SENT")
            if status_returned == "MANUAL_REQUIRED":
                reason = result.get("error_message") or "Intervention humaine requise (CAPTCHA ou Login)"
                application.mark_as_manual_required(reason)
                NotificationService.create_notification(
                    db=db,
                    user_id=user_id,
                    type=NotificationType.APPLICATION_FAILED,
                    message=f"Action requise pour {job_offer.title} chez {job_offer.company} : {reason}.",
                    related_application_id=application.id
                )
            else:
                application.mark_as_sent()
                NotificationService.create_notification(
                    db=db,
                    user_id=user_id,
                    type=NotificationType.APPLICATION_SENT,
                    message=f"Candidature approuvée et traitée pour {job_offer.title} chez {job_offer.company}.",
                    related_application_id=application.id
                )
        else:
            reason = result.get("error_message") or "Erreur d'exécution de l'agent web"
            application.mark_as_failed(reason)
            NotificationService.create_notification(
                db=db,
                user_id=user_id,
                type=NotificationType.APPLICATION_FAILED,
                message=f"Échec de l'envoi pour {job_offer.title} chez {job_offer.company} : {reason}.",
                related_application_id=application.id
            )

        db.commit()
        db.refresh(application)
        return application

    @staticmethod
    def run_agent(
        application_id: uuid.UUID,
        user_id: uuid.UUID,
        application_channel: IApplicationChannel,
        db: Session
    ) -> Application:
        application = db.get(Application, application_id)
        if not application:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidature non trouvée")

        if application.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accès non autorisé : cette candidature appartient à un autre utilisateur."
            )

        match = db.get(Match, application.match_id)
        cv = db.get(CV, match.cv_id)
        job_offer = db.get(JobOffer, match.job_offer_id)

        personal_info, experiences, skill_names = _fetch_cv_enrichment(db, cv.id)
        candidate_email = personal_info.email if personal_info else None

        result = application_channel.submit(
            application, cv, job_offer,
            candidate_email=candidate_email,
            match=match,
            personal_info=personal_info,
            experiences=experiences,
            skills=skill_names
        )

        application.cover_letter = result.get("cover_letter")
        application.execution_logs = result.get("execution_logs")
        application.screenshots = result.get("screenshots")

        if result.get("success"):
            status_returned = result.get("status", "SENT")
            if status_returned == "MANUAL_REQUIRED":
                reason = result.get("error_message") or "Intervention humaine requise"
                application.mark_as_manual_required(reason)
            else:
                application.mark_as_sent()
        else:
            reason = result.get("error_message") or "Erreur d'exécution de l'agent web"
            application.mark_as_failed(reason)

        db.commit()
        db.refresh(application)
        return application

    @staticmethod
    def reject_application(
        application_id: uuid.UUID,
        user_id: uuid.UUID,
        reason: Optional[str],
        db: Session
    ) -> Application:
        # 1. Fetch application
        application = db.get(Application, application_id)
        if not application:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidature non trouvée")

        # 2. Check ownership
        if application.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accès non autorisé : cette candidature appartient à un autre utilisateur."
            )

        # 3. Check transition
        if application.status != ApplicationStatus.PENDING_VALIDATION:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Impossible de rejeter une candidature dans l'état : {application.status}."
            )

        # 4. Reject
        application.reject(reason)
        db.commit()
        db.refresh(application)
        return application

    @staticmethod
    def get_applications(
        db: Session,
        user_id: uuid.UUID,
        status_filter: Optional[ApplicationStatus] = None
    ) -> List[Application]:
        query = db.query(Application).filter_by(user_id=user_id)
        if status_filter:
            query = query.filter_by(status=status_filter)
        return query.order_by(Application.created_at.desc()).all()
