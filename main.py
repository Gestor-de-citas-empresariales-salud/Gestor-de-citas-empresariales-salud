from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from api.agenda_router import router as agenda_router
from api.cita_router import router as cita_router
from api.auth_router import router as auth_router, RBACMiddleware
from api.especialidad_router import router as especialidad_router
from api.paciente_router import router as paciente_router
from api.profesional_router import router as profesional_router
from api.sede_router import router as sede_router

app = FastAPI(title="Gestor de citas empresariales salud")

# Pacientes
app.include_router(paciente_router)

# Profesionales
app.include_router(profesional_router)

# Especialidades
app.include_router(especialidad_router)

# Agendas
app.include_router(agenda_router)

# Sedes
app.include_router(sede_router)

# Citas
app.include_router(cita_router)

# Autenticación y permisos
app.add_middleware(RBACMiddleware)
app.include_router(auth_router)


# Capturador global
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    mensaje = "Datos o parámetros inválidos"
    errors = exc.errors()

    if errors:
        err = errors[0]
        msg_original = err.get("msg", "")
        # Obtenemos la ubicación del campo del input
        loc = err.get("loc", [])
        campo = loc[-1] if loc else "campo"

        # Traducción y mapeo del error de Pydantic
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
