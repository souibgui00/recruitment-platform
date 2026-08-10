from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict
from job_sourcing.models import JobSource

@dataclass
class JobOfferDTO:
    """Brute data format extracted directly from external platforms."""
    raw_title: str
    raw_company: str
    raw_location: str
    raw_description: str
    raw_url: str
    raw_posted_date: Optional[str] = None

class IJobConnector(ABC):
    """Port interface defining job listing fetch capabilities."""
    
    @abstractmethod
    def fetch_offers(self, source: JobSource, keywords: str) -> List[JobOfferDTO]:
        """Fetch offers from source platform based on keywords."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Returns True if the connector is currently operational."""
        pass

import random

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0.1 Mobile/15E148 Safari/604.1"
]

def get_random_user_agent() -> str:
    return random.choice(USER_AGENTS)

# Shared plug-and-play connectors registry
_connectors: Dict[str, IJobConnector] = {}

def register_connector(name: str, connector: IJobConnector):
    """Register a connector by its lowercase name."""
    _connectors[name.lower()] = connector

def get_connector(name: str) -> IJobConnector:
    """Retrieve connector by name."""
    name_lower = name.lower()
    if name_lower not in _connectors:
        raise ValueError(f"No connector registered for source: {name}")
    return _connectors[name_lower]
