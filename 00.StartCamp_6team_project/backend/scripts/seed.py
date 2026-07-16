import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.ingest import run_ingest  # noqa: E402

logging.basicConfig(level=logging.INFO)


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        total = run_ingest(db)
        print(f"적재 완료: 총 {total}건")
    finally:
        db.close()


if __name__ == "__main__":
    main()
