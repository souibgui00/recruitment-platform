import requests
import xml.etree.ElementTree as ET
from typing import List
from job_sourcing.connectors.base import IJobConnector, JobOfferDTO
from job_sourcing.models import JobSource


class IndeedRSSConnector(IJobConnector):
    """
    Adapter for the Indeed public RSS feed.
    Indeed publishes public RSS feeds for job searches — no authentication required.
    Returns real job listings from France and Tunisia.
    """

    BASE_URL = "https://fr.indeed.com/rss"

    def is_available(self) -> bool:
        try:
            r = requests.get(
                self.BASE_URL,
                params={"q": "python", "l": "france"},
                headers={"User-Agent": "Mozilla/5.0 (compatible; RSS reader)"},
                timeout=10
            )
            return r.status_code == 200
        except Exception:
            return False

    def fetch_offers(self, source: JobSource, keywords: str) -> List[JobOfferDTO]:
        offers = []
        # Fetch for 2 locations: France and Tunisia
        locations = ["france", "tunisie"]

        for location in locations:
            try:
                params = {
                    "q": keywords,
                    "l": location,
                    "fromage": "14",   # Last 14 days
                    "sort": "date",
                }
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "application/rss+xml, application/xml, text/xml",
                }
                r = requests.get(self.BASE_URL, params=params, headers=headers, timeout=15)
                r.raise_for_status()

                root = ET.fromstring(r.content)
                channel = root.find("channel")
                if channel is None:
                    continue

                for item in channel.findall("item"):
                    title = item.findtext("title", "").strip()
                    link = item.findtext("link", "").strip()
                    description = item.findtext("description", "").strip()
                    pub_date = item.findtext("pubDate", "").strip()

                    # Company is often embedded in title as "Job Title - Company"
                    company = ""
                    if " - " in title:
                        parts = title.rsplit(" - ", 1)
                        title = parts[0].strip()
                        company = parts[1].strip()

                    if not title or not link:
                        continue

                    offers.append(JobOfferDTO(
                        raw_title=title,
                        raw_company=company or "N/A",
                        raw_location=location.capitalize(),
                        raw_description=description,
                        raw_url=link,
                        raw_posted_date=pub_date if pub_date else None,
                    ))

            except Exception as e:
                print(f"[IndeedRSSConnector] Error for location '{location}': {e}")
                continue

        return offers
