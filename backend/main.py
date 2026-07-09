from fastapi import FastAPI

app = FastAPI(title="Plateforme de recrutement IA")


@app.get("/health")
def health_check():
    return {"status": "ok"}