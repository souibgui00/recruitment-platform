import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from shared.database import SessionLocal
from job_sourcing.models import JobSource
from job_sourcing.services.collection_service import JobCollectionService

logger = logging.getLogger("apscheduler")
scheduler = BackgroundScheduler()

def autonomous_job_sourcing_task():
    """Tâche périodique automatique exécutée par l'agent de recrutement."""
    logger.info("Agent autonome : démarrage de la collecte automatique périodique d'offres...")
    db = SessionLocal()
    try:
        active_sources = db.query(JobSource).filter_by(is_active=True).all()
        if not active_sources:
            logger.info("Agent autonome : aucune source active trouvée.")
            return

        # Mots-clés par défaut pour peupler la base de manière générale
        keywords = "developer python react javascript devops"
        
        for source in active_sources:
            try:
                logger.info(f"Agent autonome : collecte en cours pour la source '{source.name}'...")
                JobCollectionService.run_collection(source, keywords, db)
                logger.info(f"Agent autonome : collecte réussie pour '{source.name}'")
            except Exception as ex:
                logger.error(f"Agent autonome : erreur lors de la collecte de '{source.name}': {ex}")
    finally:
        db.close()
    logger.info("Agent autonome : collecte automatique terminée.")

def start_scheduler():
    """Démarre le scheduler en arrière-plan."""
    if not scheduler.running:
        # On planifie la tâche toutes les 6 heures
        scheduler.add_job(
            autonomous_job_sourcing_task,
            trigger=IntervalTrigger(hours=6),
            id="autonomous_job_sourcing",
            name="Collecte automatique d'offres d'emploi par l'agent",
            replace_existing=True
        )
        scheduler.start()
        logger.info("Agent autonome : Planificateur de tâches démarré (Fréquence : toutes les 6 heures).")

def stop_scheduler():
    """Arrête proprement le scheduler."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Agent autonome : Planificateur de tâches arrêté.")
