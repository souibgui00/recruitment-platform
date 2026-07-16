from typing import List
from sentence_transformers import SentenceTransformer
from cv_management.ports.embedding_provider import IEmbeddingProvider

_model = None

class E5EmbeddingProvider(IEmbeddingProvider):
    def __init__(self):
        global _model
        if _model is None:
            _model = SentenceTransformer("intfloat/multilingual-e5-large")
        self.model = _model

    def embed(self, text: str) -> List[float]:
        embedding = self.model.encode(f"query: {text}")
        return embedding.tolist()
