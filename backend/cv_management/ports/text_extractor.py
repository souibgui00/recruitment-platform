from abc import ABC, abstractmethod
from fastapi import UploadFile

class ITextExtractor(ABC):
    @abstractmethod
    def extract_text(self, file_path: str) -> str:
        """Extract text content from a file."""
        pass
