from fastapi import APIRouter

router = APIRouter()


@router.get("/{session_id}/status")
async def status(session_id: str):
    return {"status": "not implemented"}


@router.get("/{session_id}/hypotheses")
async def hypotheses(session_id: str):
    return {"status": "not implemented"}
