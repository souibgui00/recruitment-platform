from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from cv_management.router import router as cv_router

app = FastAPI(title="Plateforme de recrutement IA")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cv_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}