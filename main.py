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
    mensaje = "Datos o parámetros inválidos"
    errors = exc.errors()

    if errors:
        err = errors[0]
        msg_original = err.get("msg", "")
        # Obtenemos la ubicación del campo (ej. ['body', 'contactos', 0, 'parentesco'] -> 'parentesco')
        loc = err.get("loc", [])
        campo = loc[-1] if loc else "campo"

        # Traducción y mapeo amigable en español según el error de Pydantic
        if "at least" in msg_original or "min_length" in err.get("type", ""):
            mensaje = f"El campo '{campo}' es obligatorio o muy corto"
        elif "string type" in msg_original or "field required" in msg_original:
            mensaje = f"El campo '{campo}' es obligatorio"
        elif "Value error" in msg_original:
            # Limpiamos nuestro ValueError personalizado del dominio
            mensaje = msg_original.replace("Value error, ", "", 1)
        else:
            mensaje = f"Error en el campo '{campo}': {msg_original}"

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "mensaje": mensaje,
            "data": None,
            "success": False,
        },
    )

@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0", "environment": "development"}