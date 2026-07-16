from sqlalchemy.orm import Session
from cv_management.models import CV, Experience, Education, CVSkill, PersonalInfo, CVEmbedding, CVStatus
from cv_management.date_parsing import parse_flexible_date
from cv_management.skill_normalization import normalize_skill
from cv_management.schemas import ParsedCVData

from cv_management.ports.text_extractor import ITextExtractor
from cv_management.ports.llm_extractor import ILLMExtractor
from cv_management.ports.embedding_provider import IEmbeddingProvider

from cv_management.adapters.pdf_text_extractor import PdfTextExtractor
from cv_management.adapters.groq_llm_extractor import GroqLLMExtractor
from cv_management.adapters.e5_embedding_provider import E5EmbeddingProvider

def parse_cv(
    cv: CV, 
    db: Session,
    text_extractor: ITextExtractor,
    llm_extractor: ILLMExtractor,
    embedding_provider: IEmbeddingProvider
) -> CV:
    cv.status = CVStatus.PARSING
    db.commit()

    try:
        raw_text = text_extractor.extract_text(cv.raw_file_url)
        raw_data_dict = llm_extractor.extract_structured_data(raw_text)
        parsed_data = ParsedCVData(**raw_data_dict)

        personal_info = PersonalInfo(
            cv_id=cv.id,
            full_name=parsed_data.full_name,
            email=parsed_data.email,
            phone=parsed_data.phone,
            location=parsed_data.location,
        )
        db.add(personal_info)

        for exp in parsed_data.experiences:
            experience = cv.add_experience(
                title=exp.title,
                company=exp.company,
                start_date=parse_flexible_date(exp.start_date),
                end_date=parse_flexible_date(exp.end_date) if exp.end_date else None,
                description=exp.description,
                is_current=exp.is_current
            )
            db.add(experience)

        for edu in parsed_data.education:
            education = Education(
                cv_id=cv.id,
                degree=edu.degree,
                institution=edu.institution,
                field=edu.field,
                start_date=parse_flexible_date(edu.start_date),
                end_date=parse_flexible_date(edu.end_date) if edu.end_date else None,
            )
            db.add(education)

        for skill_name in parsed_data.skills:
            skill = normalize_skill(skill_name, db)
            cv_skill = cv.add_skill(
                skill_id=skill.id,
                proficiency="UNKNOWN",
                source="EXPLICIT"
            )
            db.add(cv_skill)

        embedding_vector = embedding_provider.embed(raw_text)
        cv_embedding = CVEmbedding(
            cv_id=cv.id,
            vector=embedding_vector,
            model_name="intfloat/multilingual-e5-large",
        )
        db.add(cv_embedding)

        cv.mark_as_parsed()
        db.commit()
        db.refresh(cv)
    except Exception as e:
        db.rollback()
        cv.mark_as_failed(reason=str(e))
        db.add(cv)  # Re-attach cv to session after rollback
        db.commit()
        db.refresh(cv)

    return cv