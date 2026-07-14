from sqlalchemy.orm import Session

from cv_management.models import CV, Experience, Education, CVSkill, PersonalInfo
from cv_management.text_extraction import extract_text_from_pdf
from cv_management.llm_extraction import extract_cv_data
from cv_management.date_parsing import parse_flexible_date
from cv_management.skill_normalization import normalize_skill
from cv_management.models import CVEmbedding
from cv_management.embedding_generation import generate_embedding


def parse_cv(cv: CV, db: Session) -> CV:
    raw_text = extract_text_from_pdf(cv.raw_file_url)
    parsed_data = extract_cv_data(raw_text)

    personal_info = PersonalInfo(
        cv_id=cv.id,
        full_name=parsed_data.full_name,
        email=parsed_data.email,
        phone=parsed_data.phone,
        location=parsed_data.location,
    )
    db.add(personal_info)

    for exp in parsed_data.experiences:
        experience = Experience(
            cv_id=cv.id,
            title=exp.title,
            company=exp.company,
            start_date=parse_flexible_date(exp.start_date),
            end_date=parse_flexible_date(exp.end_date),
            description=exp.description,
            is_current=exp.is_current,
        )
        db.add(experience)

    for edu in parsed_data.education:
        education = Education(
            cv_id=cv.id,
            degree=edu.degree,
            institution=edu.institution,
            field=edu.field,
            start_date=parse_flexible_date(edu.start_date),
            end_date=parse_flexible_date(edu.end_date),
        )
        db.add(education)

    for skill_name in parsed_data.skills:
        skill = normalize_skill(skill_name, db)
        cv_skill = CVSkill(
            cv_id=cv.id,
            skill_id=skill.id,
            proficiency="UNKNOWN",
            source="EXPLICIT",
        )
        db.add(cv_skill)
    embedding_vector = generate_embedding(raw_text)
    cv_embedding = CVEmbedding(
        cv_id=cv.id,
        vector=embedding_vector,
        model_name="intfloat/multilingual-e5-large",
    )
    db.add(cv_embedding)
    cv.status = "PARSED"
    db.commit()
    db.refresh(cv)

    return cv