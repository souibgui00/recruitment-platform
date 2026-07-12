from fastapi import FastAPI

from cv_management.router import router as cv_router

app = FastAPI(title="Plateforme de recrutement IA")

app.include_router(cv_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}