from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.gzip import GZipMiddleware

from .database import Base, SessionLocal, engine
from .ingest import seed_if_empty
from .migrations import migrate_auth_ownership, migrate_community_courses
from .routers import auth, chat, community, contents, geo, planner, realtime

Base.metadata.create_all(bind=engine)
migrate_auth_ownership(engine)
migrate_community_courses(engine)

app = FastAPI(title="SeoulMySoulMate API")

# 1. TrustedHostMiddleware 추가 (필요 시)
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["myseoulmate.onrender.com", "localhost", "127.0.0.1"]
)

# 2. CORS 미들웨어 (가장 중요)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://ssafystartcamp-git-main-macboy5s-projects.vercel.app",
        "https://ssafystartcamp.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"], # OPTIONS를 포함한 모든 메서드 허용
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=500)

app.include_router(contents.router)
app.include_router(auth.router)
app.include_router(community.router)
app.include_router(chat.router)
app.include_router(planner.router)
app.include_router(realtime.router)
app.include_router(geo.router)


@app.on_event("startup")
def on_startup() -> None:
    db = SessionLocal()
    try:
        seed_if_empty(db)
    finally:
        db.close()


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
