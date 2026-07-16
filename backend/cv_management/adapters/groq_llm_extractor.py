import os
import json
from groq import Groq
from typing import Dict, Any
from cv_management.ports.llm_extractor import ILLMExtractor

class GroqLLMExtractor(ILLMExtractor):
    def __init__(self):
        self.client = Groq(api_key=os.environ["GROQ_API_KEY"])

    def extract_structured_data(self, raw_text: str) -> Dict[str, Any]:
        prompt = f"""Tu es un assistant qui extrait des informations structurées d'un CV.

Voici le texte brut d'un CV :
---
{raw_text}
---

Réponds UNIQUEMENT avec un objet JSON respectant exactement cette structure, sans aucun texte avant ou après :
{{
  "full_name": "string",
  "email": "string ou null",
  "phone": "string ou null",
  "location": "string ou null",
  "experiences": [
    {{"title": "string", "company": "string", "start_date": "string", "end_date": "string ou null", "description": "string ou null", "is_current": true ou false}}
  ],
  "education": [
    {{"degree": "string", "institution": "string", "field": "string ou null", "start_date": "string", "end_date": "string ou null"}}
  ],
  "skills": ["string", "string"]
}}
"""
        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        raw_json = response.choices[0].message.content
        return json.loads(raw_json)
