from collections import deque

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import seoul_geo
from ..database import get_db
from .realtime import get_areas_congestion

router = APIRouter(prefix="/api/geo", tags=["geo"])

_CONGESTION_SEVERITY = {"여유": 0, "보통": 1, "약간 붐빔": 2, "붐빔": 3}


def _fill_from_neighbours(districts: dict[str, dict]) -> None:
    """구에 직접 관측지역이 없으면 인접 구를 따라가며 값을 찾아 채운다.

    바로 이웃도 데이터가 없을 수 있으므로(예: 노원구-중랑구가 서로 이웃이면서
    둘 다 비어있는 경우) 너비 우선 탐색으로 데이터가 있는 가장 가까운 구를 찾는다.
    """
    adjacency = seoul_geo.gu_adjacency()
    for gu_name in adjacency:
        if gu_name in districts:
            continue
        visited = {gu_name}
        queue = deque(adjacency.get(gu_name, []))
        while queue:
            candidate = queue.popleft()
            if candidate in visited:
                continue
            visited.add(candidate)
            if candidate in districts:
                districts[gu_name] = {
                    **districts[candidate],
                    "inherited": True,
                    "source_gu": candidate,
                }
                break
            queue.extend(adjacency.get(candidate, []))


@router.get("/seoul-districts")
def seoul_districts() -> dict:
    """25개 자치구 경계(행정동 GeoJSON을 sggnm 기준으로 병합)."""
    return seoul_geo.gu_boundaries_geojson()


@router.get("/seoul-districts/congestion")
def seoul_districts_congestion(
    refresh: bool = False,
    db: Session = Depends(get_db),
) -> dict:
    """구 안에 있는 관측지역들 중 가장 혼잡한 단계를 그 구의 대표값으로 집계."""
    areas_payload = get_areas_congestion(db, refresh)

    by_gu: dict[str, list[dict]] = {}
    for item in areas_payload.get("items", []):
        gu_name = seoul_geo.find_gu(item["longitude"], item["latitude"])
        if not gu_name:
            continue
        by_gu.setdefault(gu_name, []).append(item)

    districts: dict[str, dict] = {}
    for gu_name, items in by_gu.items():
        worst = max(
            items, key=lambda item: _CONGESTION_SEVERITY.get(item["congestion"]["level"], 0)
        )
        districts[gu_name] = {
            "level": worst["congestion"]["level"],
            "emoji": worst["congestion"]["emoji"],
            "message": worst["congestion"]["message"],
            "area_count": len(items),
        }

    _fill_from_neighbours(districts)

    return {
        "fetched_at": areas_payload.get("fetched_at"),
        "configured": areas_payload.get("configured", False),
        "cached": areas_payload.get("cached", False),
        "districts": districts,
    }
