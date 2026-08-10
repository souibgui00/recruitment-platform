from job_sourcing.connectors.base import IJobConnector, JobOfferDTO, register_connector
from job_sourcing.connectors.remotive.connector import RemotiveConnector
from job_sourcing.connectors.arbeitnow.connector import ArbeitnowConnector
from job_sourcing.connectors.jobicy.connector import JobicyConnector
from job_sourcing.connectors.themuse.connector import TheMuseConnector
from job_sourcing.connectors.bundesagentur.connector import BundesagenturConnector
from job_sourcing.connectors.welcometothejungle.algolia_connector import WelcomeToTheJungleAlgoliaConnector

# Register free official API connectors
register_connector("remotive", RemotiveConnector())
register_connector("arbeitnow", ArbeitnowConnector())
register_connector("jobicy", JobicyConnector())
register_connector("themuse", TheMuseConnector())
register_connector("bundesagentur", BundesagenturConnector())

# Register Algolia-based connector for WTTJ (reverse-engineered public search API)
register_connector("welcometothejungle", WelcomeToTheJungleAlgoliaConnector())


