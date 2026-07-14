import os
from groq import Groq

client = Groq(api_key=os.environ["GROQ_API_KEY"])


def test_llm_connection() -> str:
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": "Réponds juste par le mot: OK"}],
    )
    return response.choices[0].message.content