import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from api.review import router as review_router
from api.poc import router as poc_router
from api.reader import router as reader_router
from api.research import router as research_router

logging.basicConfig(level=settings.log_level)

app = FastAPI(title="PaperCourt API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(review_router, prefix="/review")
app.include_router(poc_router, prefix="/poc")
app.include_router(reader_router, prefix="/read")
app.include_router(research_router, prefix="/research")


@app.get("/health")
async def health():
    return {"status": "ok"}
