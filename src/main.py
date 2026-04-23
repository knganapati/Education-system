from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from src.database import init_db
from src.config import settings
from src.routers import auth, batches, sessions, attendance, summary, monitoring

app = FastAPI(
    title="SkillBridge Attendance API",
    description="Backend API for the SkillBridge state-level skilling programme attendance management system.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow all origins for prototype; lock down in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Custom Validation Error Handler ─────────────────────────────────────────

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Return 422 with descriptive error messages instead of raw Pydantic output."""
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"] if loc != "body")
        errors.append(f"{field}: {error['msg']}" if field else error["msg"])
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": errors},
    )


# ─── Startup ──────────────────────────────────────────────────────────────────

@app.on_event("startup")
def on_startup():
    """Create database tables on startup and verify connection."""
    print(f"🚀 Initializing system with environment: {settings.APP_ENV}")
    try:
        init_db()
        print("✅ Database tables created/verified on Neon PostgreSQL.")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")



# ─── Routers ──────────────────────────────────────────────────────────────────

app.include_router(auth.router)
app.include_router(batches.router)
app.include_router(sessions.router)
app.include_router(attendance.router)
app.include_router(summary.router)
app.include_router(monitoring.router)


# ─── Root ─────────────────────────────────────────────────────────────────────

@app.get("/", tags=["Root"])
def root():
    return {
        "name": "SkillBridge Attendance API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "ok",
    }


@app.get("/health", tags=["Root"])
def health():
    return {"status": "ok"}
