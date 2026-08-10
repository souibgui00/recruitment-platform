import requests
from typing import List
from job_sourcing.connectors.base import IJobConnector, JobOfferDTO
from job_sourcing.models import JobSource

class JobicyConnector(IJobConnector):
    """
    Adapter for the Jobicy public API.
    Docs: https://jobicy.com/api/v2/remote-jobs
    100% legal, free, no authentication required.
    Returns real remote job listings.
    """

    BASE_URL = "https://jobicy.com/api/v2/remote-jobs"

    def is_available(self) -> bool:
        try:
            r = requests.get(self.BASE_URL, params={"count": 1}, timeout=10)
            return r.status_code == 200
        except Exception:
            return False

    def fetch_offers(self, source: JobSource, keywords: str) -> List[JobOfferDTO]:
        try:
            offers = []
            params = {"count": 50}
            r = requests.get(self.BASE_URL, params=params, timeout=15)
            r.raise_for_status()
            data = r.json()
            jobs = data.get("jobs", [])

            keywords_list = [k.lower() for k in keywords.split()] if keywords else []

            for job in jobs:
                title = job.get("jobTitle", "")
                description = job.get("jobDescription", "")
                combined = f"{title} {description}".lower()

                # Filter by keyword
                if keywords_list and not any(kw in combined for kw in keywords_list):
                    continue

                offers.append(JobOfferDTO(
                    raw_title=title,
                    raw_company=job.get("companyName", ""),
                    raw_location=job.get("jobGeo", "Remote"),
                    raw_description=description,
                    raw_url=job.get("url", ""),
                    raw_posted_date=job.get("pubDate", None),
                ))

            return offers

        except Exception as e:
            print(f"[JobicyConnector] Error fetching offers: {e}")
            return []
