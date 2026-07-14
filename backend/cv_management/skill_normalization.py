from sqlalchemy.orm import Session

from cv_management.models import Skill


def normalize_skill(raw_skill_name: str, db: Session) -> Skill:
    clean_name = raw_skill_name.strip()

    existing = db.query(Skill).filter(Skill.canonical_name == clean_name).first()
    if existing:
        return existing

    new_skill = Skill(canonical_name=clean_name, category="unknown")
    db.add(new_skill)
    db.flush()
    return new_skill