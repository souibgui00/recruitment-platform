from typing import List
import urllib.parse
from datetime import datetime
from playwright.sync_api import sync_playwright

from job_sourcing.connectors.base import IJobConnector, JobOfferDTO
from job_sourcing.models import JobSource


class TanitJobsScraper(IJobConnector):
    """
    Playwright-based scraper for TanitJobs to bypass 403 Forbidden errors.
    """

    BASE_URL = "https://www.tanitjobs.com/jobs/"

    def is_available(self) -> bool:
        # For protected sites, assume available to prevent blocking collection prematurely
        return True

    def fetch_offers(self, source: JobSource, keywords: str) -> List[JobOfferDTO]:
        offers = []
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                # Create a context with a realistic user agent
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={"width": 1920, "height": 1080}
                )
                page = context.new_page()

                search_url = f"{self.BASE_URL}?search={urllib.parse.quote(keywords)}"
                
                # Navigate and wait for network to be somewhat idle
                page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
                
                # Wait for job listings to appear (class often used by tanitjobs is 'job-listing' or 'job-title')
                # But since we don't know the exact class today, we wait a fixed 3s just to be safe if no selector is known
                page.wait_for_timeout(3000)
                
                # Scrape logic
                # Typical structure: <article class="job-listing"> ...
                # Let's extract all links that look like job posts
                # Usually hrefs contain '/job/' or '/emploi/'
                elements = page.locator("article, .job-listing, .media").all()

                for el in elements:
                    try:
                        title_el = el.locator("h2, h3, .job-title").first
                        if title_el.count() == 0:
                            continue
                            
                        title = title_el.inner_text().strip()
                        
                        link_el = el.locator("a[href*='/job/'], a[href*='/emploi/']").first
                        url = link_el.get_attribute("href") if link_el.count() > 0 else ""
                        
                        if not url.startswith("http"):
                            url = "https://www.tanitjobs.com" + url

                        company_el = el.locator(".company-name, .job-company").first
                        company = company_el.inner_text().strip() if company_el.count() > 0 else "Unknown"

                        location_el = el.locator(".location, .job-location").first
                        location = location_el.inner_text().strip() if location_el.count() > 0 else "Tunisie"

                        desc_el = el.locator(".description, .job-description").first
                        description = desc_el.inner_text().strip() if desc_el.count() > 0 else ""

                        if title and url:
                            offers.append(JobOfferDTO(
                                raw_title=title,
                                raw_company=company,
                                raw_location=location,
                                raw_description=description,
                                raw_url=url,
                                raw_posted_date=datetime.utcnow().isoformat()
                            ))
                    except Exception as e:
                        print(f"[TanitJobsScraper] Error parsing element: {e}")
                        continue

                browser.close()
        except Exception as e:
            print(f"[TanitJobsScraper] Playwright error: {e}")

        return offers
