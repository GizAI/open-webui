from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from .config_extension import init_extended_config
from open_webui.rooibos.routers import (
    corpsearch)

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

    app.include_router(corpsearch.router, prefix="/api/v1/corpsearch", tags=["corpsearch"])

    # Initialize extended configurations
    init_extended_config(app)
    
    # Add custom middlewares
    app.add_middleware(CustomHeaderMiddleware)
    
    # You can add more middleware here
    
    # Add new routes if needed
    @app.get("/api/naver-map-key")
    async def get_naver_map_key():
        return {"api_key": app.state.config.NAVER_MAP_API_KEY}
    
    return app