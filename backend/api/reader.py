from fastapi import APIRouter

router = APIRouter()


@router.get("/{job_id}/status")
async def status(job_id: str):
    return {"status": "not implemented"}


@router.get("/{job_id}/annotations")
async def annotations(job_id: str):
    return {"status": "not implemented"}
