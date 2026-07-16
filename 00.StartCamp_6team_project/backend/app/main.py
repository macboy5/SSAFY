from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

from .database import Base, SessionLocal, engine
from .ingest import seed_if_empty
from .migrations import migrate_auth_ownership, migrate_community_courses
from .routers import auth, chat, community, contents, geo, planner, realtime

Base.metadata.create_all(bind=engine)
migrate_auth_ownership(engine)
migrate_community_courses(engine)

app = FastAPI(title="SeoulMySoulMate API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://ssafystartcamp-git-main-macboy5s-projects.vercel.app",
        "https://ssafystartcamp.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
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
