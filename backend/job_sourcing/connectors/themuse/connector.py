import requests
from typing import List
from datetime import datetime

from job_sourcing.connectors.base import IJobConnector, JobOfferDTO
from job_sourcing.models import JobSource


class TheMuseConnector(IJobConnector):
    """
    Connector for The Muse — 100% free, public API, no authentication required.
    https://www.themuse.com/developers/api/v2
    Returns real job listings from tech companies globally.
    """

    BASE_URL = "https://www.themuse.com/api/public/jobs"
    CATEGORIES = ["Software Engineer", "Data Science", "IT", "Engineering", "Product", "Design"]

    def is_available(self) -> bool:
        try:
            r = requests.get(self.BASE_URL, params={"page": 0}, timeout=10)
            return r.status_code == 200
        except Exception:
            return False

    def fetch_offers(self, source: JobSource, keywords: str) -> List[JobOfferDTO]:
        offers = []
        keywords_list = [k.lower() for k in keywords.split()] if keywords else []

        try:
            for category in self.CATEGORIES:
                try:
                    r = requests.get(
                        self.BASE_URL,
                        params={"page": 0, "category": category, "level": "Mid Level,Senior Level,Entry Level"},
                        timeout=15
                    )
                    r.raise_for_status()
                    jobs = r.json().get("results", [])

                    for job in jobs:
                        title = job.get("name", "").strip()
                        company = job.get("company", {}).get("name", "N/A")
                        contents = job.get("contents", "")
                        refs = job.get("refs", {})
                        url = refs.get("landing_page", "")
                        locations = job.get("locations", [])
                        location = locations[0].get("name", "Remote") if locations else "Remote"
                        publication_date = job.get("publication_date", "")

                        # Keyword filter
                        combined = f"{title} {contents}".lower()
                        if keywords_list and not any(kw in combined for kw in keywords_list):
                            continue

                        if not title or not url:
                            continue

                        offers.append(JobOfferDTO(
                            raw_title=title,
                            raw_company=company,
                            raw_location=location,
                            raw_description=contents[:1000] if contents else f"{title} at {company}",
                            raw_url=url,
                            raw_posted_date=publication_date if publication_date else None,
                        ))

                except Exception as e:
                    print(f"[TheMuse] Error for category '{category}': {e}")
                    continue

        except Exception as e:
            print(f"[TheMuse] Error fetching offers: {e}")

        return offers
