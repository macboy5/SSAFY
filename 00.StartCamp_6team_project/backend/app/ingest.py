import json
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import DATA_DIR
from .models import TourContent

logger = logging.getLogger(__name__)


def _to_row_fields(category: str, item: dict) -> dict:
    return {
        "contentid": item.get("contentid", ""),
        "contenttypeid": item.get("contenttypeid", ""),
        "category": category,
        "title": item.get("title", ""),
        "addr1": item.get("addr1", ""),
        "addr2": item.get("addr2", ""),
        "tel": item.get("tel", ""),
        "firstimage": item.get("firstimage", ""),
        "firstimage2": item.get("firstimage2", ""),
        "mapx": item.get("mapx", ""),
        "mapy": item.get("mapy", ""),
        "areacode": item.get("areacode", ""),
        "sigungucode": item.get("sigungucode", ""),
        "cat1": item.get("cat1", ""),
        "cat2": item.get("cat2", ""),
        "cat3": item.get("cat3", ""),
        "raw_json": json.dumps(item, ensure_ascii=False),
    }


def run_ingest(db: Session) -> int:
    existing_ids = {row[0] for row in db.execute(select(TourContent.contentid))}
    total_processed = 0

    for path in sorted(DATA_DIR.glob("서울_*.json")):
        with path.open(encoding="utf-8") as f:
            data = json.load(f)

        category = data.get("contentType", path.stem.replace("서울_", ""))
        items = data.get("items", [])

        for item in items:
            contentid = item.get("contentid")
            if not contentid:
                continue
            fields = _to_row_fields(category, item)
            if contentid in existing_ids:
                db.query(TourContent).filter(TourContent.contentid == contentid).update(fields)
            else:
                db.add(TourContent(**fields))
                existing_ids.add(contentid)
            total_processed += 1

        db.commit()
        logger.info("적재 완료: %s (%d건)", path.name, len(items))

    return total_processed


def seed_if_empty(db: Session) -> None:
    count = db.execute(select(TourContent.id).limit(1)).first()
    if count is None:
        total = run_ingest(db)
        logger.info("초기 데이터 적재: 총 %d건", total)
