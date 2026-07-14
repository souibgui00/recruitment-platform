from sentence_transformers import SentenceTransformer

_model = None


def get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("intfloat/multilingual-e5-large")
    return _model


def generate_embedding(text: str) -> list[float]:
    model = get_embedding_model()
    embedding = model.encode(f"query: {text}")
    return embedding.tolist()