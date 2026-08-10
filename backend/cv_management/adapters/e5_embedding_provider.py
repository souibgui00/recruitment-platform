import os
import threading
from typing import List
from sentence_transformers import SentenceTransformer
from cv_management.ports.embedding_provider import IEmbeddingProvider

_model = None
_model_lock = threading.Lock()
_LOCAL_MODEL_PATH = "/app/model_cache"
_HF_MODEL_NAME = "intfloat/multilingual-e5-large"


class E5EmbeddingProvider(IEmbeddingProvider):
    def get_model(self) -> SentenceTransformer:
        global _model
        if _model is None:
            with _model_lock:
                # Double-check inside lock
                if _model is None:
                    local_file = os.path.join(_LOCAL_MODEL_PATH, "model.safetensors")
                    if os.path.exists(local_file):
                        print(f"[E5Provider] Loading model from local cache: {_LOCAL_MODEL_PATH}")
                        _model = SentenceTransformer(_LOCAL_MODEL_PATH)
                    else:
                        print(f"[E5Provider] Loading model from HuggingFace Hub: {_HF_MODEL_NAME}")
                        _model = SentenceTransformer(_HF_MODEL_NAME)
        return _model

    def embed(self, text: str) -> List[float]:
        model = self.get_model()
        embedding = model.encode(f"passage: {text}")
        return embedding.tolist()
