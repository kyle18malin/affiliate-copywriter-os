"""
Affiliate Copywriter OS - Main Application
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
import os

from backend.database import init_db, async_session
from backend.api.routes import router
from backend.services.rss_service import init_default_feeds
from backend.services.niche_service import init_default_niches
from backend.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database and default data on startup"""
    await init_db()
    
    # Initialize defaults
    async with async_session() as db:
        await init_default_niches(db)
        await init_default_feeds(db)
    
    print("✅ Affiliate Copywriter OS initialized!")
    print(f"📰 Default RSS feeds configured")
    print(f"🎯 Default niches: {', '.join(settings.default_niches)}")
    
    yield


app = FastAPI(
    title="Affiliate Copywriter OS",
    description="AI-powered hook generation for affiliate ads",
    version="1.0.0",
    lifespan=lifespan
)

# CORS for frontend (allow all origins for Railway)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(router, prefix="/api")

# Serve frontend static files
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")

if os.path.exists(frontend_path):
    # Mount assets directory
    assets_path = os.path.join(frontend_path, "assets")
    if os.path.exists(assets_path):
        app.mount("/assets", StaticFiles(directory=assets_path), name="assets")
    
    @app.get("/", response_class=HTMLResponse)
    async def serve_index():
        """Serve the React frontend index"""
        index_path = os.path.join(frontend_path, "index.html")
        if os.path.exists(index_path):
            with open(index_path, "r") as f:
                return HTMLResponse(content=f.read())
        return HTMLResponse(content="<h1>Frontend not built. Run: cd frontend && npm run build</h1>")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve the React frontend"""
        # Skip API routes
        if full_path.startswith("api"):
            return None
        
        file_path = os.path.join(frontend_path, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        
        # Return index.html for SPA routing
        index_path = os.path.join(frontend_path, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        
        return HTMLResponse(content="<h1>Not found</h1>", status_code=404)
else:
    @app.get("/")
    async def no_frontend():
        """Placeholder when frontend not built"""
        return HTMLResponse(content="""
        <html>
        <head><title>Affiliate Copywriter OS</title></head>
        <body style="font-family: system-ui; background: #0a0a0f; color: white; padding: 40px;">
            <h1>🚀 Affiliate Copywriter OS</h1>
            <p>API is running! Frontend needs to be built.</p>
            <p>API docs: <a href="/docs" style="color: #6366f1;">/docs</a></p>
        </body>
        </html>
        """)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)
