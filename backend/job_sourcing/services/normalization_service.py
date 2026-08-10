import re
import hashlib
from datetime import datetime
from typing import Optional
from bs4 import BeautifulSoup

from job_sourcing.connectors.base import JobOfferDTO
from job_sourcing.models import JobOffer, JobSource, ContractType, OfferStatus

class JobNormalizationService:
    @staticmethod
    def clean_html(text: str) -> str:
        """Strip HTML tags and clean up whitespace."""
        if not text:
            return ""
        # Remove HTML formatting
        soup = BeautifulSoup(text, "html.parser")
        cleaned = soup.get_text(separator=" ")
        # Clean extra spaces and newlines
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned.strip()

    @staticmethod
    def detect_contract_type(description: str, title: str) -> Optional[ContractType]:
        """Detect contract type from title or description text using heuristics."""
        combined_text = f"{title} {description}".upper()
        
        if re.search(r'\b(CDI|DURÉE INDÉTERMINÉE|PERMANENT)\b', combined_text):
            return ContractType.CDI
        if re.search(r'\b(CDD|DURÉE DÉTERMINÉE|TEMPORAIRE|CONTRACT)\b', combined_text):
            return ContractType.CDD
        if re.search(r'\b(STAGE|STAGIAIRE|INTERN|INTERNSHIP)\b', combined_text):
            return ContractType.STAGE
        if re.search(r'\b(FREELANCE|INDÉPENDANT|CONTRACTOR|CONSULTANT EXTERNE)\b', combined_text):
            return ContractType.FREELANCE
            
        return None

    @classmethod
    def compute_fingerprint(cls, raw_url: str, title: str, company: str) -> str:
        """Compute a unique SHA-256 hash for deduplication."""
        unique_string = f"{raw_url.strip().lower()}:{title.strip().lower()}:{company.strip().lower()}"
        return hashlib.sha256(unique_string.encode('utf-8')).hexdigest()

    @classmethod
    def normalize(cls, dto: JobOfferDTO, source: JobSource) -> JobOffer:
        """Convert a raw JobOfferDTO into a clean domain JobOffer entity."""
        title = cls.clean_html(dto.raw_title)
        company = cls.clean_html(dto.raw_company)
        description = cls.clean_html(dto.raw_description)
        location = cls.clean_html(dto.raw_location) if dto.raw_location else None
        
        fingerprint = cls.compute_fingerprint(dto.raw_url, title, company)
        contract_type = cls.detect_contract_type(description, title)
        
        # Simple date parsing logic
        posted_at = None
        if dto.raw_posted_date:
            try:
                # Expect ISO or common format, fallback to now if unparseable
                posted_at = datetime.fromisoformat(dto.raw_posted_date)
            except ValueError:
                posted_at = datetime.utcnow()
        else:
            posted_at = datetime.utcnow()

        return JobOffer(
            source_id=source.id,
            source_url=dto.raw_url,
            fingerprint=fingerprint,
            title=title,
            company=company,
            location=location,
            description=description,
            contract_type=contract_type,
            posted_at=posted_at,
            collected_at=datetime.utcnow(),
            status=OfferStatus.NEW
        )
