from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from cv_management.router import router as cv_router
from user_management.router import router as auth_router
from job_sourcing.router import router as jobs_router
from matching.router import router as matching_router
from applications.router import router as applications_router
from notifications.router import router as notifications_router
from job_sourcing.scheduler import start_scheduler, stop_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Démarrer le planificateur de tâches de l'agent
    start_scheduler()
    yield
    # Arrêter proprement au shutdown
    stop_scheduler()

import os
from fastapi.staticfiles import StaticFiles

# Ensure static directory exists
os.makedirs("static/screenshots", exist_ok=True)

app = FastAPI(title="Plateforme de recrutement IA", redirect_slashes=False, lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cv_router)
app.include_router(auth_router)
app.include_router(jobs_router)
app.include_router(matching_router)
app.include_router(applications_router)
app.include_router(notifications_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}