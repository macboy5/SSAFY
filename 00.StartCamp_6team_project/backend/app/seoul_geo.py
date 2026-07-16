"""서울시 행정동 경계 → 자치구 경계 파생.

원본 GeoJSON은 raqoon886/Local_HangJeongDong의 서울특별시 행정동(425개) 파일이며,
프론트엔드가 정적 자산으로 그대로 서빙하는 파일을 백엔드도 그대로 읽어 같은 파일을
두 곳에 중복 보관하지 않는다. 자치구(25개) 경계는 여기서 동 폴리곤을 ``sggnm``
기준으로 병합(dissolve)해 1회만 계산하고 캐시한다.
"""

import json
from threading import Lock

from shapely.geometry import Point, mapping, shape
from shapely.ops import unary_union

from .config import REPO_ROOT

DONG_GEOJSON_PATH = REPO_ROOT / "frontend" / "public" / "geo" / "seoul_dong.geojson"

_lock = Lock()
_gu_polygons: dict[str, object] | None = None
_gu_geojson: dict | None = None
_gu_adjacency: dict[str, list[str]] | None = None

# Small buffer (~11m at Seoul's latitude) so gu boundaries that share an edge
# but don't touch to floating-point precision are still detected as adjacent.
_ADJACENCY_BUFFER_DEGREES = 0.0001


def _load_gu_polygons() -> dict[str, object]:
    global _gu_polygons
    with _lock:
        if _gu_polygons is not None:
            return _gu_polygons

        with DONG_GEOJSON_PATH.open(encoding="utf-8") as f:
            data = json.load(f)

        shapes_by_gu: dict[str, list] = {}
        for feature in data["features"]:
            gu_name = feature["properties"].get("sggnm")
            if not gu_name:
                continue
            shapes_by_gu.setdefault(gu_name, []).append(shape(feature["geometry"]))

        _gu_polygons = {
            gu_name: unary_union(geoms) for gu_name, geoms in shapes_by_gu.items()
        }
        return _gu_polygons


def find_gu(longitude: float, latitude: float) -> str | None:
    point = Point(longitude, latitude)
    for gu_name, polygon in _load_gu_polygons().items():
        if polygon.contains(point):
            return gu_name
    return None


def gu_adjacency() -> dict[str, list[str]]:
    """Which gu polygons border each other, for filling in gu's with no data
    from a neighbour instead of leaving them blank.
    """
    global _gu_adjacency
    with _lock:
        if _gu_adjacency is not None:
            return _gu_adjacency

    polygons = _load_gu_polygons()
    buffered = {name: polygon.buffer(_ADJACENCY_BUFFER_DEGREES) for name, polygon in polygons.items()}
    names = list(polygons)
    adjacency: dict[str, list[str]] = {name: [] for name in names}
    for i, name_a in enumerate(names):
        for name_b in names[i + 1 :]:
            if buffered[name_a].intersects(buffered[name_b]):
                adjacency[name_a].append(name_b)
                adjacency[name_b].append(name_a)

    with _lock:
        _gu_adjacency = adjacency
        return _gu_adjacency


def gu_boundaries_geojson() -> dict:
    global _gu_geojson
    with _lock:
        if _gu_geojson is not None:
            return _gu_geojson

    _load_gu_polygons()
    with _lock:
        _gu_geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"sggnm": gu_name},
                    "geometry": mapping(polygon),
                }
                for gu_name, polygon in _gu_polygons.items()
            ],
        }
        return _gu_geojson
