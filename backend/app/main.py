from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .database import STORAGE_DIR, init_db
from .routers import auth, internships, profiles


BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = STORAGE_DIR / "uploads"
FRONTEND_DIST_DIR = BASE_DIR.parent / "frontend" / "dist"
PUBLIC_DIR = BASE_DIR.parent / "public"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="InternMatch API",
    description="Student internship discovery and profile management API.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(internships.router, prefix="/api")
app.include_router(profiles.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
if FRONTEND_DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST_DIR / "assets"), name="assets")


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def serve_index() -> FileResponse:
    index_file = _resolve_frontend_index()
    if not index_file.exists():
        raise HTTPException(
            status_code=404,
            detail="Frontend build not found. Run `npm run build` in the frontend directory.",
        )
    return FileResponse(index_file)


@app.get("/{full_path:path}", include_in_schema=False)
def serve_spa(full_path: str) -> FileResponse:
    if full_path.startswith(("api/", "uploads/", "assets/")):
        raise HTTPException(status_code=404, detail="Not found.")

    frontend_root = _resolve_frontend_root()
    requested = frontend_root / full_path
    if requested.exists() and requested.is_file():
        return FileResponse(requested)

    index_file = _resolve_frontend_index()
    if not index_file.exists():
        raise HTTPException(
            status_code=404,
            detail="Frontend build not found. Run `npm run build` in the frontend directory.",
        )
    return FileResponse(index_file)


def _resolve_frontend_root() -> Path:
    if PUBLIC_DIR.exists():
        return PUBLIC_DIR
    return FRONTEND_DIST_DIR


def _resolve_frontend_index() -> Path:
    return _resolve_frontend_root() / "index.html"
