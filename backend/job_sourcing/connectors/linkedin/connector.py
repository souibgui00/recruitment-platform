import logging
from typing import List

from job_sourcing.connectors.base import IJobConnector, JobOfferDTO
from job_sourcing.models import JobSource

logger = logging.getLogger(__name__)

class LinkedInConnector(IJobConnector):
    """
    LinkedIn hybrid connector.
    Defines the architecture for API access and Playwright fallback,
    and returns simulated data to guarantee a robust, reliable demo.
    """
    
    def is_available(self) -> bool:
        # Mock connector is always available for testing and demos
        return True

    def fetch_offers(self, source: JobSource, keywords: str) -> List[JobOfferDTO]:
        logger.info(f"LinkedIn hybrid connector running for keywords: {keywords}")
        
        # 1. API Strategy (Simulated check)
        api_accessible = False
        if api_accessible:
            logger.info("Fetching via LinkedIn API")
            return self._fetch_via_api(source, keywords)
            
        # 2. Playwright Web Scraping Strategy (Simulated check/fallback)
        playwright_active = False
        if playwright_active:
            logger.info("Fetching via Playwright Scraper")
            return self._fetch_via_playwright(source, keywords)
            
        # 3. Hybrid Fallback (Mock data)
        logger.info("API and Playwright inactive. Falling back to local LinkedIn mock data.")
        return self._fetch_via_mock(keywords)

    def _fetch_via_api(self, source: JobSource, keywords: str) -> List[JobOfferDTO]:
        # Placeholders for future official API endpoints integrations
        return []

    def _fetch_via_playwright(self, source: JobSource, keywords: str) -> List[JobOfferDTO]:
        # Placeholders for future headless browser scraping integrations
        return []

    def _fetch_via_mock(self, keywords: str) -> List[JobOfferDTO]:
        """Realistic mock data representing actual LinkedIn search results for Tunisia & France."""
        all_mocks = [
            JobOfferDTO(
                raw_title="Data Scientist (Tunis / Hybride)",
                raw_company="InstaDeep",
                raw_location="Tunis, Tunisie",
                raw_description="Nous recherchons un ingénieur ou chercheur en Data Science pour rejoindre notre bureau de Tunis. Vous collaborerez à la recherche de pointe en LLM et renforcement par apprentissage. Profil requis : Python, PyTorch, JAX, Git, solide niveau en mathématiques.",
                raw_url="https://www.linkedin.com/jobs/view/instadeep-data-scientist-tunis",
                raw_posted_date=None
            ),
            JobOfferDTO(
                raw_title="Développeur Python Backend FastAPI",
                raw_company="Cegid",
                raw_location="Tunis, Tunisie",
                raw_description="Cegid recrute un développeur Backend Python en CDI. Vous participerez au développement de nouvelles fonctionnalités pour notre plateforme SaaS. Compétences requises : Python 3+, FastAPI, PostgreSQL, Architecture Microservices.",
                raw_url="https://www.linkedin.com/jobs/view/cegid-python-backend-tunis",
                raw_posted_date=None
            ),
            JobOfferDTO(
                raw_title="Machine Learning Engineer (NLP / RAG)",
                raw_company="Société Générale",
                raw_location="Paris, France",
                raw_description="Rejoignez notre centre d'excellence IA pour concevoir des applications sémantiques internes. Analyse de contrats, assistant virtuel intelligent, et traitement de gros volumes de documents textuels. Compétences : Python, Hugging Face, LangChain, Elasticsearch.",
                raw_url="https://www.linkedin.com/jobs/view/sg-ml-engineer-paris",
                raw_posted_date=None
            ),
            JobOfferDTO(
                raw_title="Data Engineer Senior",
                raw_company="BlaBlaCar",
                raw_location="Paris, France",
                raw_description="En tant que Data Engineer Senior, vous rejoindrez l'équipe Core Data pour maintenir notre Datalake. Compétences requises : Python, Spark, Scala, GCP, BigQuery, Airflow, dbt.",
                raw_url="https://www.linkedin.com/jobs/view/blablacar-data-engineer-senior",
                raw_posted_date=None
            )
        ]
        
        filtered = [
            job for job in all_mocks
            if keywords.lower() in job.raw_title.lower() 
            or keywords.lower() in job.raw_description.lower()
        ]
        
        return filtered if filtered else all_mocks
