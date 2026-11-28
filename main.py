from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

from api.agenda_router import router as agenda_router
from api.auth_router import RBACMiddleware, router as auth_router
from api.cita_router import router as cita_router
from api.especialidad_router import router as especialidad_router
from api.paciente_router import router as paciente_router
from api.profesional_router import router as profesional_router
from api.sede_router import router as sede_router

app = FastAPI(title="Gestor de citas empresariales salud")


@app.middleware("http")
async def validar_cita_id_vacio(request: Request, call_next):
    ruta = request.scope.get("path", "")
    metodo = request.method
    if (
        (metodo == "POST" and ruta == "/api/v1/citas//check-in")
        or (metodo == "PUT" and ruta == "/api/v1/citas//reprogramar")
        or (metodo == "DELETE" and ruta in ("/api/v1/citas/", "/api/v1/citas"))
    ):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "mensaje": "El campo 'cita_id' es obligatorio",
                "data": None,
                "success": False,
            },
        )
    return await call_next(request)


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


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version="1.0.0",
        routes=app.routes,
    )
    for path_item in openapi_schema.get("paths", {}).values():
        for operation in path_item.values():
            if isinstance(operation, dict):
                for param in operation.get("parameters", []):
                    param["required"] = False
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# Capturador global
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    mensaje = "Datos o parámetros inválidos"
    errors = exc.errors()

    if errors:
        err = errors[0]
        msg_original = err.get("msg", "")
        loc = err.get("loc", [])
        campo = loc[-1] if loc else "campo"

        if "at least" in msg_original or "min_length" in err.get("type", ""):
            mensaje = f"El campo '{campo}' es obligatorio o muy corto"
        elif "string type" in msg_original or "field required" in msg_original:
            mensaje = f"El campo '{campo}' es obligatorio"
        elif "Value error" in msg_original:
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