"""DocFlow API routes."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/healthz")
async def healthz():
    return {"status": "ok"}


# Document endpoints (stubs — implemented in later steps)
# POST   /documents
# GET    /documents/{id}
# GET    /documents/{id}/audit
# GET    /queue
# POST   /documents/{id}/decision
# POST   /policies
# POST   /internal/process
