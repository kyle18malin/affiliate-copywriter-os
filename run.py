#!/usr/bin/env python3
"""
Affiliate Copywriter OS - Run Script
"""
import uvicorn
from backend.config import settings

if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║         AFFILIATE COPYWRITER OS                           ║
    ║         AI-Powered Hook Generation                        ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    )
