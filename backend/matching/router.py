import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from shared.database import get_db
from user_management.dependencies import get_current_user
from user_management.models import User

from matching.schemas import (
    MatchResponse,
    MatchingConfigResponse,
    MatchingConfigUpdate,
)
from matching.matching_service import MatchingService
from matching.adapters.cosine_similarity_calculator import PgVectorSimilarityCalculator
from matching.adapters.groq_matching_evaluator import GroqMatchingEvaluator

router = APIRouter(prefix="/matching", tags=["matching"])

# Instantiate adapters as singletons
similarity_calculator = PgVectorSimilarityCalculator()
llm_evaluator = GroqMatchingEvaluator()


@router.post("/cv/{cv_id}/job/{job_offer_id}", response_model=MatchResponse)
def compute_single_match(
    cv_id: uuid.UUID,
    job_offer_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Compute (or recalculate) the matching score and qualitative breakdown between a CV and a Job Offer.
    """
    match = MatchingService.compute_match(
        cv_id=cv_id,
        job_offer_id=job_offer_id,
        user_id=current_user.id,
        similarity_calculator=similarity_calculator,
        llm_evaluator=llm_evaluator,
        db=db,
    )
    return match


@router.get("/cv/{cv_id}/best-matches", response_model=List[MatchResponse])
def get_best_matches_for_cv(
    cv_id: uuid.UUID,
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get top matching job offers for a specific CV sorted by compatibility score.
    """
    ranked_pairs = MatchingService.get_best_matches_for_cv(
        cv_id=cv_id,
        user_id=current_user.id,
        similarity_calculator=similarity_calculator,
        llm_evaluator=llm_evaluator,
        db=db,
        limit=limit,
        offset=offset,
    )

    response_list = []
    for match, job_offer in ranked_pairs:
        resp = MatchResponse.model_validate(match)
        resp.job_offer = {
            "id": str(job_offer.id),
            "title": job_offer.title,
            "company": job_offer.company,
            "location": job_offer.location,
            "source_url": job_offer.source_url,
            "contract_type": job_offer.contract_type.value if job_offer.contract_type else None,
            "posted_at": job_offer.posted_at.isoformat() if job_offer.posted_at else None,
        }
        response_list.append(resp)

    return response_list


@router.get("/config", response_model=MatchingConfigResponse)
def get_matching_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get current user's matching preferences configuration.
    """
    config = MatchingService.get_or_create_config(current_user.id, db)
    return config


@router.put("/config", response_model=MatchingConfigResponse)
def update_matching_config(
    payload: MatchingConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update current user's matching preferences configuration (threshold, weights).
    Guarantees that semantic_weight + llm_weight always equals 1.0.
    """
    config = MatchingService.get_or_create_config(current_user.id, db)

    if payload.threshold is not None:
        config.threshold = payload.threshold

    new_sem = payload.semantic_weight if payload.semantic_weight is not None else config.semantic_weight
    new_llm = payload.llm_weight if payload.llm_weight is not None else config.llm_weight

    if payload.semantic_weight is not None and payload.llm_weight is None:
        new_llm = round(1.0 - new_sem, 4)
    elif payload.llm_weight is not None and payload.semantic_weight is None:
        new_sem = round(1.0 - new_llm, 4)
    elif payload.semantic_weight is not None and payload.llm_weight is not None:
        if round(new_sem + new_llm, 4) != 1.0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"La somme de semantic_weight ({new_sem}) et llm_weight ({new_llm}) doit être égale à 1.0"
            )

    config.semantic_weight = new_sem
    config.llm_weight = new_llm

    db.commit()
    db.refresh(config)
    return config
