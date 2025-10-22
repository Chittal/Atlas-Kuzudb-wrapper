from fastapi import Request

def get_kuzu_manager():
    """Return shared Kuzu manager instance."""
    # Import app here to avoid circular import
    try:
        from app import app as fastapi_app
        if hasattr(fastapi_app.state, "kuzu_manager") and fastapi_app.state.kuzu_manager is not None:
            return fastapi_app.state.kuzu_manager
    except Exception:
        pass
    raise RuntimeError("Kuzu manager not initialized")
