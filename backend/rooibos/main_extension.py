from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from rooibos.config_extension import init_extended_config
from rooibos.routers import (
    corpsearch,
    mycompanies,
    folders,
    notes
)
class CustomHeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Custom-Header"] = "Custom Value"
        return response

def extend_app(app: FastAPI):
    """
    Extend the FastAPI application with additional configurations and middlewares
    
    Args:
        app (FastAPI): The main FastAPI application instance
    """

    app.include_router(corpsearch.router, prefix="/api/v1/rooibos/corpsearch", tags=["corpsearch"])
    app.include_router(mycompanies.router, prefix="/api/v1/rooibos/mycompanies", tags=["mycompanies"])
    app.include_router(folders.router, prefix="/api/v1/rooibos/folders", tags=["folders"])
    app.include_router(notes.router, prefix="/api/v1/rooibos/notes", tags=["notes"])

    # Initialize extended configurations
    init_extended_config(app)
    
    # Add custom middlewares
    # app.add_middleware(CustomHeaderMiddleware)
    
    # You can add more middleware here
    
    # Add new routes if needed
    @app.get("/api/naver-map-key")
    async def get_naver_map_key():
        return {"api_key": app.state.config.NAVER_MAP_API_KEY}
    
    return app