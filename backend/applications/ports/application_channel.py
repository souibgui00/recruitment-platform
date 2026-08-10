from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class IApplicationChannel(ABC):
    @abstractmethod
    def submit(self, application, cv, job_offer, candidate_email: Optional[str] = None, match=None, personal_info=None, experiences=None, skills=None) -> Dict[str, Any]:
        """
        Attempts to submit a job application.
        Returns a dictionary containing:
        { "success": bool, "error_message": str | None }
        Optional enrichment data:
        - match: Match object with LLM analysis (matching_points, gap_points, summary, compatibility_score)
        - personal_info: PersonalInfo object (full_name, phone, location)
        - experiences: list of Experience objects
        - skills: list of skill names
        """
        pass
