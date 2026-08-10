from typing import List
import urllib.parse
from datetime import datetime
from playwright.sync_api import sync_playwright

from job_sourcing.connectors.base import IJobConnector, JobOfferDTO
from job_sourcing.models import JobSource


class WelcomeToTheJungleScraper(IJobConnector):
    """
    Playwright-based scraper for Welcome to the Jungle.
    Bypasses anti-bot mechanisms by simulating a real browser.
    """

    BASE_URL = "https://www.welcometothejungle.com/fr/jobs"

    def is_available(self) -> bool:
        return True

    def fetch_offers(self, source: JobSource, keywords: str) -> List[JobOfferDTO]:
        offers = []
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
                    viewport={"width": 1280, "height": 800}
                )
                page = context.new_page()

                search_url = f"{self.BASE_URL}?query={urllib.parse.quote(keywords)}"
                
                # Navigate
                page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
                
                # Wait for react app to hydrate and jobs to appear
                page.wait_for_timeout(4000)
                
                # WTTJ usually uses data-testid or specific semantic classes for jobs
                # A common selector for their job cards is "li" within the jobs list, or 'a[href*="/jobs/"]'
                # Let's try to grab all links pointing to a job page
                job_links = page.locator("a[href*='/companies/'][href*='/jobs/']").all()

                for link_el in job_links:
                    try:
                        url = link_el.get_attribute("href")
                        if not url:
                            continue
                        if not url.startswith("http"):
                            url = "https://www.welcometothejungle.com" + url

                        # Get all text inside the card
                        text = link_el.inner_text()
                        lines = [line.strip() for line in text.split('\n') if line.strip()]
                        
                        if len(lines) < 2:
                            continue
                            
                        # Extremely basic heuristic to extract from card text
                        company = lines[0]
                        title = lines[1]
                        
                        location = "Remote / France"
                        if len(lines) > 2:
                            location = lines[2]

                        offers.append(JobOfferDTO(
                            raw_title=title,
                            raw_company=company,
                            raw_location=location,
                            raw_description=text,  # Put full text since we don't click into it
                            raw_url=url,
                            raw_posted_date=datetime.utcnow().isoformat()
                        ))
                    except Exception as e:
                        print(f"[WTTJScraper] Error parsing card: {e}")
                        continue
                        
                browser.close()
        except Exception as e:
            print(f"[WTTJScraper] Playwright error: {e}")

        return offers
