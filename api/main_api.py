from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.trip_routes import router as trip_router


BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
EXPORTS_DIR = BASE_DIR / "exports"


app = FastAPI(
    title="智能旅行助手 API",
    description="基于 LLM + Tools 的智能旅行规划后端服务",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(trip_router)

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
app.mount("/exports", StaticFiles(directory=EXPORTS_DIR), name="exports")


@app.get("/", include_in_schema=False)
def home_page():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/history", include_in_schema=False)
def history_page():
    return FileResponse(FRONTEND_DIR / "history.html")


@app.get("/trip-detail", include_in_schema=False)
def trip_detail_page():
    return FileResponse(FRONTEND_DIR / "detail.html")


@app.get("/api", include_in_schema=False)
def api_root():
    return {
        "message": "智能旅行助手 API 已启动",
        "docs": "/docs"
    }
