import requests
from typing import List
import urllib.parse

from job_sourcing.connectors.base import IJobConnector, JobOfferDTO
from job_sourcing.models import JobSource


class BundesagenturConnector(IJobConnector):
    """
    Connector for the German Federal Employment Agency (Bundesagentur für Arbeit).
    100% free, official public API — no authentication or API key required.
    Endpoint: https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/app/jobs
    Returns real job listings from Germany, many international/remote tech roles.
    """

    BASE_URL = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/app/jobs"
    JOB_DETAIL_URL = "https://www.arbeitsagentur.de/jobsuche/jobdetail/"

    def is_available(self) -> bool:
        try:
            r = requests.get(
                self.BASE_URL,
                params={"was": "developer", "size": 1},
                headers={"X-API-Key": "jobboerse-jobsuche"},
                timeout=10
            )
            return r.status_code == 200
        except Exception:
            return False

    def fetch_offers(self, source: JobSource, keywords: str) -> List[JobOfferDTO]:
        offers = []
        try:
            params = {
                "was": keywords or "developer",
                "size": 50,
                "angebotsart": 1,  # Job offers only (not internships/training)
            }
            r = requests.get(
                self.BASE_URL,
                params=params,
                headers={"X-API-Key": "jobboerse-jobsuche"},
                timeout=15
            )
            r.raise_for_status()
            data = r.json()
            jobs = data.get("stellenangebote", [])

            for job in jobs:
                try:
                    title = job.get("titel", "").strip()
                    company = job.get("arbeitgeber", "N/A")
                    
                    # Location
                    arbeitsort = job.get("arbeitsort", {})
                    city = arbeitsort.get("ort", "")
                    country = arbeitsort.get("land", "Deutschland")
                    location = f"{city}, {country}" if city else country

                    # URL — construct from reference number (refnr)
                    ref_nr = job.get("refnr", "")
                    url = f"{self.JOB_DETAIL_URL}{ref_nr}" if ref_nr else ""

                    # Description from available fields
                    eintrittsdatum = job.get("eintrittsdatum", "")
                    modifikations_timestamp = job.get("modifikationsTimestamp", "")
                    beruf = job.get("beruf", "")
                    description = f"{beruf}. {title} chez {company}. Localisation: {location}."

                    if not title:
                        continue

                    offers.append(JobOfferDTO(
                        raw_title=title,
                        raw_company=company,
                        raw_location=location,
                        raw_description=description,
                        raw_url=url,
                        raw_posted_date=modifikations_timestamp if modifikations_timestamp else None,
                    ))

                except Exception as e:
                    print(f"[Bundesagentur] Error parsing job: {e}")
                    continue

        except Exception as e:
            print(f"[Bundesagentur] Error fetching offers: {e}")

        return offers
