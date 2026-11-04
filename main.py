from fastapi import FastAPI

app = FastAPI(title="Gestor de citas empresariales salud")


@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0", "environment": "development"}