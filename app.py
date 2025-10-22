from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from helper.kuzu_db_helper import KuzuSkillGraph
from config import app_config

from routes.skills import router as skills_router

import os
from dotenv import load_dotenv
load_dotenv()


app = FastAPI(title="KuzuDB Wrapper", description="KuzuDB Wrapper for learning roadmap skills")
kuzu_manager = None
# Initialize shared Kuzu manager and agent in startup events to avoid multi-process locks
@app.on_event("startup")
def on_startup():
    try:
        app.state.kuzu_manager = KuzuSkillGraph("skills_graph.db")
        global kuzu_manager
        kuzu_manager = app.state.kuzu_manager
        print("✅ KuzuDB manager initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize KuzuDB manager: {e}")

@app.on_event("shutdown")
def on_shutdown():
    try:
        if hasattr(app.state, "kuzu_manager") and app.state.kuzu_manager:
            app.state.kuzu_manager.close()
    except Exception:
        pass

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (including AgentCore)
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Specific methods
    allow_headers=["*"],  # Allows all headers (including X-API-Key)
)

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "KuzuDB Wrapper API is running"}


# Include routers with prefix
prefix = app_config.url_prefix if app_config.url_prefix else ""
app.include_router(skills_router, prefix=prefix)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8008))  # Use PORT env var or default to 8008
    uvicorn.run(app, host="0.0.0.0", port=port)
