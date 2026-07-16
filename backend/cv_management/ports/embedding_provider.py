from abc import ABC, abstractmethod
from typing import List

class IEmbeddingProvider(ABC):
    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """Generate vector embedding for the given text."""
        pass
