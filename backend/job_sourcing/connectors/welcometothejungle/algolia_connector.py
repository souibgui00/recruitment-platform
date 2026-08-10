import requests
from typing import List
from datetime import datetime

from job_sourcing.connectors.base import IJobConnector, JobOfferDTO
from job_sourcing.models import JobSource


class WelcomeToTheJungleAlgoliaConnector(IJobConnector):
    """
    Connector for Welcome to the Jungle using their public Algolia search API.
    The API key and Application ID are the same public search-only keys embedded
    in their frontend bundle — fully public and read-only.
    Endpoint reverse-engineered from browser network traffic on /fr/jobs.
    """

    ALGOLIA_URL = "https://csekhvms53-dsn.algolia.net/1/indexes/wk_cms_jobs_production/query"
    ALGOLIA_APP_ID = "CSEKHVMS53"
    ALGOLIA_API_KEY = "4bd8f6215d0cc52b26430765769e65a0"
    BASE_JOB_URL = "https://www.welcometothejungle.com/fr/companies/{company_slug}/jobs/{job_slug}"

    def is_available(self) -> bool:
        try:
            r = requests.post(
                self.ALGOLIA_URL,
                headers=self._headers(),
                json={"query": "test", "hitsPerPage": 1},
                timeout=10
            )
            return r.status_code == 200
        except Exception:
            return False

    def fetch_offers(self, source: JobSource, keywords: str) -> List[JobOfferDTO]:
        offers = []
        try:
            payload = {
                "query": keywords,
                "hitsPerPage": 50,
                "attributesToRetrieve": [
                    "name",
                    "organization",
                    "contract_type_names",
                    "office",
                    "remote",
                    "slug",
                    "objectID",
                    "sectors",
                    "profession",
                    "published_at",
                    "description",
                ]
            }

            r = requests.post(
                self.ALGOLIA_URL,
                headers=self._headers(),
                json=payload,
                timeout=15
            )
            r.raise_for_status()
            hits = r.json().get("hits", [])

            for hit in hits:
                try:
                    title = hit.get("name", "").strip()
                    if not title:
                        continue

                    org = hit.get("organization", {})
                    company = org.get("name", "N/A")
                    company_slug = org.get("slug") or org.get("reference", "")

                    job_slug = hit.get("slug", hit.get("objectID", ""))
                    url = self.BASE_JOB_URL.format(
                        company_slug=company_slug,
                        job_slug=job_slug
                    ) if company_slug and job_slug else f"https://www.welcometothejungle.com/fr/jobs/{job_slug}"

                    office = hit.get("office", {})
                    location_parts = [office.get("city", ""), office.get("country", "")]
                    location = ", ".join(p for p in location_parts if p) or "France"

                    remote = hit.get("remote", "")
                    if remote == "full":
                        location = f"Remote ({location})"
                    elif remote == "partial":
                        location = f"Hybrid ({location})"

                    # Contract type
                    contract_names = hit.get("contract_type_names", {})
                    contract_str = contract_names.get("fr", "") or contract_names.get("en", "")

                    # Description from profession + sectors
                    profession = hit.get("profession", {})
                    profession_name = ""
                    if profession:
                        prof_names = profession.get("name", {})
                        profession_name = prof_names.get("fr") or prof_names.get("en", "")

                    sectors = hit.get("sectors", [])
                    sector_names = []
                    for s in sectors:
                        s_name = s.get("name", {})
                        sector_names.append(s_name.get("fr") or s_name.get("en", ""))

                    description = f"{profession_name}. Secteurs: {', '.join(sector_names)}. Contrat: {contract_str}. Lieu: {location}."

                    # published_at is already an ISO datetime string (e.g. "2026-07-25T00:00:00.000+02:00")
                    posted_str = hit.get("published_at")

                    offers.append(JobOfferDTO(
                        raw_title=title,
                        raw_company=company,
                        raw_location=location,
                        raw_description=description,
                        raw_url=url,
                        raw_posted_date=posted_str,
                    ))

                except Exception as e:
                    print(f"[WTTJAlgolia] Error parsing hit: {e}")
                    continue

        except Exception as e:
            print(f"[WTTJAlgolia] Error fetching from Algolia: {e}")

        return offers

    def _headers(self) -> dict:
        return {
            "x-algolia-application-id": self.ALGOLIA_APP_ID,
            "x-algolia-api-key": self.ALGOLIA_API_KEY,
            "Referer": "https://www.welcometothejungle.com/",
            "Content-Type": "application/json",
        }
