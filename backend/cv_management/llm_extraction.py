import os
from groq import Groq
import json
from cv_management.schemas import ParsedCVData

client = Groq(api_key=os.environ["GROQ_API_KEY"])


def test_llm_connection() -> str:
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": "Réponds juste par le mot: OK"}],
    )
    return response.choices[0].message.content



def extract_cv_data(raw_text: str) -> ParsedCVData:
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

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )

    raw_json = response.choices[0].message.content
    parsed_dict = json.loads(raw_json)
    return ParsedCVData(**parsed_dict)