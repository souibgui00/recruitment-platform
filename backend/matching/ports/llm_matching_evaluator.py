from abc import ABC, abstractmethod
from typing import Dict, Any


class ILLMMatchingEvaluator(ABC):
    """
    Port interface for qualitative LLM evaluation of candidate CV vs job offer.
    """

    @abstractmethod
    def evaluate(self, cv_summary: str, job_offer_summary: str) -> Dict[str, Any]:
        """
        Evaluates the qualitative alignment between a CV summary and a Job Offer summary.
        Returns a dict containing:
          - llm_score: float (0.0 to 100.0)
          - matching_points: list[str]
          - gap_points: list[str]
          - summary: str
        """
        ...
