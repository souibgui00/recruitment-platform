import uuid
from typing import List, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from cv_management.models import CV, PersonalInfo, CVSkill, Experience, Skill
from job_sourcing.models import JobOffer
from matching.models import Match, MatchingConfig
from matching.ports.similarity_calculator import IEmbeddingSimilarityCalculator
from matching.ports.llm_matching_evaluator import ILLMMatchingEvaluator


class MatchingService:

    @staticmethod
    def compute_llm_score(matching_points: List[str], gap_points: List[str]) -> float:
        """
        Compute LLM score based on the number of matching points and gap points.
        Base: 55, +10 per matching point (max +40), -12 per gap point (max -48).
        Result bounded between 0.0 and 100.0.
        """
        base_score = 55.0
        bonus = min(len(matching_points), 4) * 10.0
        penalty = min(len(gap_points), 4) * 12.0
        score = base_score + bonus - penalty
        return max(0.0, min(100.0, score))

    @staticmethod
    def get_or_create_config(user_id: uuid.UUID, db: Session) -> MatchingConfig:
        """
        Get existing MatchingConfig for user or create default config on the fly.
        """
        config = db.query(MatchingConfig).filter_by(user_id=user_id).first()
        if not config:
            config = MatchingConfig(
                user_id=user_id,
                threshold=70.0,
                semantic_weight=0.6,
                llm_weight=0.4
            )
            db.add(config)
            db.commit()
            db.refresh(config)
        return config

    @staticmethod
    def compute_match(
        cv_id: uuid.UUID,
        job_offer_id: uuid.UUID,
        user_id: uuid.UUID,
        similarity_calculator: IEmbeddingSimilarityCalculator,
        llm_evaluator: ILLMMatchingEvaluator,
        db: Session
    ) -> Match:
        """
        Compute or update the match score and qualitative evaluation between a CV and a JobOffer.
        """
        cv = db.get(CV, cv_id)
        if not cv:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CV non trouvé")

        # 1. Security Check: Ownership verification
        if cv.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accès non autorisé : ce CV appartient à un autre utilisateur."
            )

        job_offer = db.get(JobOffer, job_offer_id)
        if not job_offer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offre d'emploi non trouvée")

        config = MatchingService.get_or_create_config(user_id, db)

        # 2. Calculate vector similarity
        try:
            semantic_sim = similarity_calculator.calculate_single_similarity(cv_id, job_offer_id, db)
        except ValueError as ve:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(ve))

        # 3. Build enriched summaries for LLM prompt
        personal_info = db.query(PersonalInfo).filter_by(cv_id=cv_id).first()
        name = personal_info.full_name if personal_info else "Candidat"
        
        experiences = db.query(Experience).filter_by(cv_id=cv_id).all()
        exp_summary = ", ".join([f"{e.title} chez {e.company}" for e in experiences]) if experiences else "Non spécifiée"

        # Explicit skills extraction from CVSkill / Skill
        cv_skills_rows = (
            db.query(Skill.canonical_name)
            .join(CVSkill, CVSkill.skill_id == Skill.id)
            .filter(CVSkill.cv_id == cv_id)
            .all()
        )
        skills_list = [s[0] for s in cv_skills_rows]
        skills_str = ", ".join(skills_list) if skills_list else "Non spécifiées"

        req_skills = job_offer.required_skills or "Non spécifiées"

        cv_summary = f"Candidat: {name}. Compétences: {skills_str}. Expériences: {exp_summary}."
        job_summary = f"Titre: {job_offer.title}. Entreprise: {job_offer.company}. Lieu: {job_offer.location}. Compétences requises: {req_skills}. Description: {job_offer.description[:600]}"

        # 3. Call LLM evaluator
        assessment = llm_evaluator.evaluate(cv_summary, job_summary)

        matching_points = assessment.get("matching_points", [])
        gap_points = assessment.get("gap_points", [])

        # 4. Calculate local LLM score
        llm_score = MatchingService.compute_llm_score(matching_points, gap_points)

        # 4. Calculate weighted compatibility score (0 to 100)
        # compatibility_score = (semantic_sim * 100 * semantic_weight) + (llm_score * llm_weight)
        comp_score = (semantic_sim * 100.0 * config.semantic_weight) + (llm_score * config.llm_weight)
        comp_score = round(max(0.0, min(100.0, comp_score)), 2)

        # 5. Upsert Match record
        match = db.query(Match).filter_by(cv_id=cv_id, job_offer_id=job_offer_id).first()
        if not match:
            match = Match(
                cv_id=cv_id,
                job_offer_id=job_offer_id,
                semantic_similarity=round(semantic_sim, 4),
                llm_score=llm_score,
                compatibility_score=comp_score,
                matching_points=assessment.get("matching_points", []),
                gap_points=assessment.get("gap_points", []),
                summary=assessment.get("summary", "")
            )
            db.add(match)
        else:
            match.semantic_similarity = round(semantic_sim, 4)
            match.llm_score = llm_score
            match.compatibility_score = comp_score
            match.matching_points = assessment.get("matching_points", [])
            match.gap_points = assessment.get("gap_points", [])
            match.summary = assessment.get("summary", "")

        db.commit()
        db.refresh(match)
        return match

    @staticmethod
    def get_best_matches_for_cv(
        cv_id: uuid.UUID,
        user_id: uuid.UUID,
        similarity_calculator: IEmbeddingSimilarityCalculator,
        llm_evaluator: ILLMMatchingEvaluator,
        db: Session,
        limit: int = 10,
        offset: int = 0
    ) -> List[Tuple[Match, JobOffer]]:
        """
        Find best matching job offers for a given CV, calculating top vector matches and returning ranked scores.
        """
        cv = db.get(CV, cv_id)
        if not cv:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CV non trouvé")

        # Security Check: Ownership verification
        if cv.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accès non autorisé : ce CV appartient à un autre utilisateur."
            )

        config = MatchingService.get_or_create_config(user_id, db)

        # Retrieve top vector candidates using SQL pgvector
        top_candidates = similarity_calculator.get_top_matching_job_offers(
            cv_id=cv_id,
            db=db,
            limit=limit * 2,  # Fetch wider sample for ranking
            threshold=0.0
        )

        results = []
        for job_offer_id, sim_score in top_candidates:
            # Check if match already computed
            match = db.query(Match).filter_by(cv_id=cv_id, job_offer_id=job_offer_id).first()
            if not match:
                # Compute match on the fly for top candidate
                try:
                    match = MatchingService.compute_match(
                        cv_id, job_offer_id, user_id, similarity_calculator, llm_evaluator, db
                    )
                except Exception as e:
                    print(f"[MatchingService] Skipping candidate match error: {e}")
                    continue

            job_offer = db.get(JobOffer, job_offer_id)
            if match and job_offer and match.compatibility_score >= config.threshold:
                results.append((match, job_offer))

        # Sort descending by compatibility score
        results.sort(key=lambda x: x[0].compatibility_score, reverse=True)
        return results[offset : offset + limit]
