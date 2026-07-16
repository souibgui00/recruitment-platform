from abc import ABC, abstractmethod
from typing import Dict, Any

class ILLMExtractor(ABC):
    @abstractmethod
    def extract_structured_data(self, raw_text: str) -> Dict[str, Any]:
        """Extract structured JSON data from raw CV text."""
        pass
