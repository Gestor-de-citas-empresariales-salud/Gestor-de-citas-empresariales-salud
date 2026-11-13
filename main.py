from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from api.paciente_router import router as paciente_router

app = FastAPI(title="Gestor de citas empresariales salud")

# Registrar el router de la HU-001
app.include_router(paciente_router)

# Capturador global
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "mensaje": "Los datos o parámetros proporcionados son inválidos o faltan campos requeridos",
            "data": None,
            "success": False
        }
    )

@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0", "environment": "development"}