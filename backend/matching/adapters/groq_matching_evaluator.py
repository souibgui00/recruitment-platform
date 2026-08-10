import os
import json
from groq import Groq
from typing import Dict, Any
from matching.ports.llm_matching_evaluator import ILLMMatchingEvaluator
from matching.schemas import MatchAssessmentData


class GroqMatchingEvaluator(ILLMMatchingEvaluator):
    """
    Adapter implementing qualitative CV-to-Job offer alignment evaluation using Groq LLM (Llama-3.3-70b-versatile).
    """

    def __init__(self):
        self.api_key = os.environ.get("GROQ_API_KEY", "")
        self.client = Groq(api_key=self.api_key) if self.api_key else None

    def evaluate(self, cv_summary: str, job_offer_summary: str) -> Dict[str, Any]:
        if not self.client:
            # Fallback if no API key is set
            return {
                "matching_points": ["Compétences techniques générales alignées."],
                "gap_points": ["Évaluation qualitative approfondie non disponible (clé API non configurée)."],
                "summary": "Correspondance sémantique calculée.",
                "score": 50
            }

        prompt = f"""Tu es un expert RH et recruteur technique senior.
Ton rôle est d'évaluer la compatibilité entre le CV d'un candidat et une offre d'emploi.

PROFIL CANDIDAT (CV) :
---
{cv_summary}
---

OFFRE D'EMPLOI :
---
{job_offer_summary}
---

Réponds STRICTEMENT avec un objet JSON valide suivant exactement ce schéma (l'exemple ci-dessous est juste un format) :
{{
  "matching_points": [
    "Point fort 1 (ex: Maîtrise de Python et FastAPI)",
    "Point fort 2 (ex: Expérience en environnement Agile)"
  ],
  "gap_points": [
    "Point à améliorer 1 (ex: Aucune mention de Docker ou Kubernetes)",
    "Point à améliorer 2 (ex: 2 ans d'expérience au lieu des 5 ans demandés)"
  ],
  "summary": "Résumé concis en 1 ou 2 phrases expliquant pourquoi le profil correspond ou non.",
  "score": 75
}}

IMPORTANT : Le champ "score" doit être un entier entre 0 et 100 représentant ta note globale de compatibilité.
"""

        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            raw_json = response.choices[0].message.content
            parsed_data = json.loads(raw_json)
            # Validate with Pydantic
            validated = MatchAssessmentData(**parsed_data)
            return validated.model_dump()
        except Exception as e:
            print(f"[GroqMatchingEvaluator] Error evaluating match: {e}")
            return {
                "matching_points": ["Analyse partielle disponible."],
                "gap_points": [f"Erreur d'analyse LLM: {str(e)}"],
                "summary": "Correspondance sémantique calculée."
            }
