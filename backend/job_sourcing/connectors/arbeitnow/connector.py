import requests
from typing import List
from job_sourcing.connectors.base import IJobConnector, JobOfferDTO
from job_sourcing.models import JobSource


class ArbeitnowConnector(IJobConnector):
    """
    Adapter for the Arbeitnow public API.
    Docs: https://www.arbeitnow.com/api/job-board-api
    100% legal, free, no authentication required.
    Returns real European job listings.
    """

    BASE_URL = "https://www.arbeitnow.com/api/job-board-api"

    def is_available(self) -> bool:
        try:
            r = requests.get(self.BASE_URL, timeout=10)
            return r.status_code == 200
        except Exception:
            return False

    def fetch_offers(self, source: JobSource, keywords: str) -> List[JobOfferDTO]:
        try:
            offers = []
            # Arbeitnow paginates — fetch pages 1 and 2 (up to 48 offers)
            for page in range(1, 3):
                params = {"page": page}
                r = requests.get(self.BASE_URL, params=params, timeout=15)
                r.raise_for_status()
                data = r.json()
                jobs = data.get("data", [])

                if not jobs:
                    break

                # Filter by keyword in title or description
                keywords_list = [k.lower() for k in keywords.split()] if keywords else []
                for job in jobs:
                    title = job.get("title", "")
                    description = job.get("description", "")
                    tags = " ".join(job.get("tags", []))
                    combined = f"{title} {description} {tags}".lower()

                    # Match if ANY of the keywords are in the text
                    if keywords_list and not any(kw in combined for kw in keywords_list):
                        continue

                    location = job.get("location", "Remote")
                    if job.get("remote", False) and not location:
                        location = "Remote"

                    offers.append(JobOfferDTO(
                        raw_title=title,
                        raw_company=job.get("company_name", ""),
                        raw_location=location,
                        raw_description=description,
                        raw_url=job.get("url", ""),
                        raw_posted_date=str(job.get("created_at", "")),
                    ))

            return offers

        except Exception as e:
            print(f"[ArbeitnowConnector] Error fetching offers: {e}")
            return []
