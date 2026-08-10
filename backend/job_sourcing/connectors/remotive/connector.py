import requests
from typing import List
from job_sourcing.connectors.base import IJobConnector, JobOfferDTO
from job_sourcing.models import JobSource


class RemotiveConnector(IJobConnector):
    """
    Adapter for the Remotive public API.
    Docs: https://remotive.com/api/remote-jobs
    100% legal, free, no authentication required.
    """

    BASE_URL = "https://remotive.com/api/remote-jobs"

    def is_available(self) -> bool:
        try:
            r = requests.get(self.BASE_URL, params={"limit": 1}, timeout=10)
            return r.status_code == 200
        except Exception:
            return False

    def fetch_offers(self, source: JobSource, keywords: str) -> List[JobOfferDTO]:
        try:
            params = {"search": keywords, "limit": 50}
            r = requests.get(self.BASE_URL, params=params, timeout=15)
            r.raise_for_status()
            data = r.json()
            jobs = data.get("jobs", [])

            offers = []
            for job in jobs:
                offers.append(JobOfferDTO(
                    raw_title=job.get("title", ""),
                    raw_company=job.get("company_name", ""),
                    raw_location=job.get("candidate_required_location", "Remote"),
                    raw_description=job.get("description", ""),
                    raw_url=job.get("url", ""),
                    raw_posted_date=job.get("publication_date", None),
                ))
            return offers

        except Exception as e:
            print(f"[RemotiveConnector] Error fetching offers: {e}")
            return []
