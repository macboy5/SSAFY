from __future__ import annotations

import json
import logging
import re
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from html import unescape
from http.cookiejar import CookieJar
from math import asin, cos, radians, sin, sqrt
from threading import Lock
from time import monotonic
from urllib.parse import quote, urlencode
from urllib.error import HTTPError, URLError
from urllib.request import HTTPCookieProcessor, Request, build_opener, urlopen
from xml.etree import ElementTree

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_seoul_citydata_api_key, get_seoul_population_api_key
from ..database import get_db
from ..models import TourContent
from ..seoul_hotspots import (
    ADDRESS_ALIASES,
    EXTRA_TITLE_ALIASES,
    HOTSPOTS_BY_CODE,
    HOTSPOTS_BY_NAME,
    SEOUL_HOTSPOTS,
    SeoulHotspot,
)

router = APIRouter(prefix="/api/realtime", tags=["realtime"])
logger = logging.getLogger(__name__)

# Integrated citydata supports additional parks/cultural areas outside the
# supplied 82-area commercial workbook. The canonical 82 registry is matched
# first; these remain as integrated-only fallbacks so existing coverage is not
# accidentally reduced.
HOTSPOT_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("잠실롯데타워·석촌호수", ("롯데월드타워", "롯데타워", "석촌호수")),
    ("송리단길·호수단길", ("송리단길", "호수단길")),
    ("국립중앙박물관·용산가족공원", ("국립중앙박물관", "용산가족공원")),
    ("서울식물원·마곡나루역", ("서울식물원", "마곡나루")),
    ("서리풀공원·몽마르뜨공원", ("서리풀공원", "몽마르뜨공원")),
    ("오목교역·목동운동장", ("오목교", "목동운동장")),
    ("신논현역·논현역", ("신논현", "논현역")),
    ("신촌·이대역", ("신촌역", "이대역", "이화여대")),
    ("창덕궁·종묘", ("창덕궁", "종묘")),
    ("광화문·덕수궁", ("덕수궁", "세종문화회관", "서울시청")),
    ("덕수궁길·정동길", ("덕수궁길", "정동길", "정동극장")),
    ("DDP(동대문디자인플라자)", ("동대문디자인플라자", "ddp")),
    ("DMC(디지털미디어시티)", ("디지털미디어시티", "dmc")),
    ("강남 MICE 관광특구", ("코엑스", "봉은사", "무역센터")),
    ("잠실 관광특구", ("롯데월드 어드벤처", "롯데월드", "잠실 관광")),
    ("홍대 관광특구", ("홍대 관광", "홍익대학교")),
    ("종로·청계 관광특구", ("청계천", "종각", "종로 관광")),
    ("동대문 관광특구", ("동대문 관광", "두타몰")),
    ("명동 관광특구", ("명동", "남산골한옥마을")),
    ("이태원 관광특구", ("이태원 관광",)),
    ("경복궁", ("경복궁", "국립고궁박물관")),
    ("보신각", ("보신각",)),
    ("서울 암사동 유적", ("암사동 유적", "선사유적")),
    ("북촌한옥마을", ("북촌한옥마을", "북촌 8경", "북촌8경")),
    ("성수카페거리", ("성수카페", "성수동 카페", "성수동2가", "성수동1가")),
    ("광장(전통)시장", ("광장시장",)),
    ("남대문시장", ("남대문시장",)),
    ("가락시장", ("가락시장",)),
    ("가로수길", ("가로수길",)),
    ("북창동 먹자골목", ("북창동",)),
    ("서촌", ("서촌", "통인시장")),
    ("신촌 스타광장", ("신촌 스타광장", "연세로")),
    ("압구정로데오거리", ("압구정로데오",)),
    ("여의도", ("더현대 서울", "여의도공원", "여의도동")),
    ("연남동", ("연남동", "경의선숲길")),
    ("영등포 타임스퀘어", ("타임스퀘어",)),
    ("용리단길", ("용리단길",)),
    ("이태원 앤틱가구거리", ("앤틱가구거리",)),
    ("익선동", ("익선동",)),
    ("인사동", ("인사동", "쌈지길")),
    ("청담동 명품거리", ("청담동 명품",)),
    ("해방촌·경리단길", ("해방촌", "경리단길")),
    ("강서한강공원", ("강서한강공원",)),
    ("광나루한강공원", ("광나루한강공원",)),
    ("광화문광장", ("광화문광장",)),
    ("난지한강공원", ("난지한강공원",)),
    ("남산공원", ("남산공원", "n서울타워", "남산서울타워")),
    ("노들섬", ("노들섬",)),
    ("뚝섬한강공원", ("뚝섬한강공원",)),
    ("망원한강공원", ("망원한강공원",)),
    ("반포한강공원", ("반포한강공원", "세빛섬")),
    ("보라매공원", ("보라매공원",)),
    ("북서울꿈의숲", ("북서울꿈의숲",)),
    ("서대문독립공원", ("서대문독립공원", "서대문형무소")),
    ("서울대공원", ("서울대공원", "서울랜드")),
    ("서울숲공원", ("서울숲",)),
    ("송현녹지광장", ("송현녹지광장", "열린송현")),
    ("아차산", ("아차산",)),
    ("안양천", ("안양천",)),
    ("양화한강공원", ("양화한강공원",)),
    ("어린이대공원", ("어린이대공원",)),
    ("여의도한강공원", ("여의도한강공원",)),
    ("여의서로", ("여의서로", "윤중로")),
    ("올림픽공원", ("올림픽공원",)),
    ("월드컵공원", ("월드컵공원", "하늘공원", "노을공원")),
    ("응봉산", ("응봉산",)),
    ("이촌한강공원", ("이촌한강공원",)),
    ("잠실종합운동장", ("잠실종합운동장", "잠실야구장")),
    ("잠실한강공원", ("잠실한강공원",)),
    ("잠원한강공원", ("잠원한강공원",)),
    ("청계산", ("청계산",)),
    ("홍제폭포", ("홍제폭포",)),
    ("고척돔", ("고척돔", "고척스카이돔")),
    ("강남역", ("강남역",)),
    ("건대입구역", ("건대입구",)),
    ("고속터미널역", ("고속터미널",)),
    ("서울역", ("서울역",)),
    ("용산역", ("용산역",)),
    ("왕십리역", ("왕십리역",)),
    ("혜화역", ("혜화역", "대학로")),
    ("삼각지역", ("삼각지역",)),
    ("홍대입구역(2호선)", ("홍대입구역",)),
    ("합정역", ("합정역",)),
    ("잠실역", ("잠실역",)),
    ("이태원역", ("이태원역",)),
    ("숭례문", ("숭례문",)),
    ("청와대", ("청와대",)),
)

INTEGRATED_AREA_CODES = {
    "삼각지역": "POI030",
    "청와대": "POI113",
}

CONGESTION_EMOJI = {
    "여유": "🟢",
    "보통": "🟡",
    "약간 붐빔": "🟠",
    "붐빔": "🔴",
}
COMMERCIAL_EMOJI = {
    "한산한 시간대": "🟢",
    "보통 시간대": "🟡",
    "바쁜 시간대": "🟠",
    "분주한 시간대": "🔴",
}

_CACHE_TTL_SECONDS = 240
_ERROR_CACHE_TTL_SECONDS = 45
_MAX_STALE_SECONDS = 1_800
_PRIMARY_BACKOFF_SECONDS = 120
_cache: dict[str, tuple[float, dict]] = {}
_error_cache: dict[str, tuple[float, dict]] = {}
_cache_lock = Lock()
_primary_retry_at = 0.0
_primary_health_lock = Lock()
_OFFICIAL_WEB_BASE = "https://data.seoul.go.kr/SeoulRtd"
_OFFICIAL_WEB_TIMEOUT_SECONDS = 3


def _normalise(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    return re.sub(r"[^0-9a-z가-힣]+", " ", value).strip()


def _compact(value: str) -> str:
    return _normalise(value).replace(" ", "")


def _phrase_match(value: str, phrase: str) -> bool:
    haystack = _normalise(value)
    needle = _normalise(phrase)
    if not haystack or not needle:
        return False
    # Token boundaries prevent 서울역 from consuming 서울역사박물관 and
    # 용산역 from consuming 신용산역. Explicit aliases cover useful variants.
    return haystack == needle or f" {needle} " in f" {haystack} "


def _title_match(value: str, phrase: str) -> bool:
    """Match a title without letting short station names consume longer words."""
    if _phrase_match(value, phrase):
        return True

    title = _normalise(value)
    alias = _normalise(phrase)
    if not _compact(alias).endswith("역"):
        return False

    # TourAPI contains franchise-style titles such as 교대역점 and 신림역점.
    # Only these explicit suffixes are accepted: 서울역사박물관, 신용산역점,
    # and 상왕십리역점 must never be folded into 서울역/용산역/왕십리역.
    pattern = rf"(?:^| ){re.escape(alias)}(?:점|지점|본점)(?: |$)"
    return re.search(pattern, title) is not None


def _registry_title_candidates(content: TourContent) -> list[tuple[int, SeoulHotspot]]:
    candidates: list[tuple[int, SeoulHotspot]] = []
    for area in SEOUL_HOTSPOTS:
        aliases = (area.area_name, *EXTRA_TITLE_ALIASES.get(area.area_code, ()))
        for alias in aliases:
            if _title_match(content.title, alias):
                exact = _normalise(content.title) == _normalise(alias)
                candidates.append((len(_compact(alias)) + (1_000 if exact else 0), area))

    return candidates


def _registry_address_match(content: TourContent) -> SeoulHotspot | None:
    candidates: list[tuple[int, SeoulHotspot]] = []
    address = _compact(f"{content.addr1} {content.addr2}")
    for area in SEOUL_HOTSPOTS:
        for alias in ADDRESS_ALIASES.get(area.area_code, ()):
            if _compact(alias) in address:
                candidates.append((len(_compact(alias)), area))
    return max(candidates, key=lambda item: item[0])[1] if candidates else None


def map_content_to_hotspot(content: TourContent) -> SeoulHotspot | None:
    # Match only areas not already represented by the canonical 82 workbook.
    # This preserves integrated citydata coverage for parks/cultural sites. All
    # title candidates compete before address fallbacks, so 여의도한강공원 is
    # not reduced to 여의도 merely because its address contains 여의도동.
    candidates = _registry_title_candidates(content)
    for area_name, aliases in HOTSPOT_RULES:
        if area_name in HOTSPOTS_BY_NAME:
            continue
        for alias in (area_name, *aliases):
            if _phrase_match(content.title, alias):
                exact = _normalise(content.title) == _normalise(alias)
                candidates.append(
                    (
                        len(_compact(alias)) + (1_000 if exact else 0),
                        SeoulHotspot(
                            "통합관측지역",
                            0,
                            INTEGRATED_AREA_CODES.get(area_name, ""),
                            area_name,
                        ),
                    )
                )
    if candidates:
        return max(candidates, key=lambda item: item[0])[1]
    return _registry_address_match(content)


def _text(parent: ElementTree.Element, tag: str) -> str:
    for element in parent.iter():
        if element.tag.rsplit("}", 1)[-1] == tag:
            return (element.text or "").strip()
    return ""


def _number(value: object) -> int:
    try:
        return int(float(str(value).replace(",", "")))
    except (AttributeError, TypeError, ValueError):
        return 0


def _float(value: object) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _distance_metres(
    longitude: float, latitude: float, other_longitude: float, other_latitude: float
) -> int:
    earth_radius = 6_371_000
    lat1, lat2 = radians(latitude), radians(other_latitude)
    delta_lat = lat2 - lat1
    delta_lon = radians(other_longitude - longitude)
    value = sin(delta_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
    return round(earth_radius * 2 * asin(sqrt(value)))


def _station_nodes(root: ElementTree.Element) -> list[ElementTree.Element]:
    return [
        node
        for node in root.iter()
        if any(child.tag.rsplit("}", 1)[-1] == "SBIKE_SPOT_NM" for child in node)
    ]


def _parse_citydata(
    xml_body: bytes,
    requested_area: str,
    requested_code: str = "",
    *,
    longitude: float | None = None,
    latitude: float | None = None,
) -> dict:
    root = ElementTree.fromstring(xml_body)
    result_code = _text(root, "CODE") or _text(root, "RESULT.CODE")
    result_message = _text(root, "MESSAGE") or _text(root, "RESULT.MESSAGE")
    if result_code and result_code != "INFO-000":
        raise ValueError(result_message or "서울시 API가 데이터를 반환하지 않았습니다.")

    level = _text(root, "AREA_CONGEST_LVL")
    population_min = _number(_text(root, "AREA_PPLTN_MIN"))
    population_max = _number(_text(root, "AREA_PPLTN_MAX"))

    stations = []
    for node in _station_nodes(root):
        name = _text(node, "SBIKE_SPOT_NM")
        if not name:
            continue
        station = {
                "name": name,
                "available_count": _number(_text(node, "SBIKE_PARKING_CNT")),
                "rack_count": _number(_text(node, "SBIKE_RACK_CNT")),
                "longitude": _text(node, "SBIKE_X"),
                "latitude": _text(node, "SBIKE_Y"),
            }
        station_longitude = _float(station["longitude"])
        station_latitude = _float(station["latitude"])
        if (
            longitude is not None
            and latitude is not None
            and station_longitude is not None
            and station_latitude is not None
        ):
            station["distance_m"] = _distance_metres(
                longitude, latitude, station_longitude, station_latitude
            )
        stations.append(station)

    distance_filter_applied = longitude is not None and latitude is not None and any(
        "distance_m" in station for station in stations
    )
    if distance_filter_applied:
        # Hotspot polygons can be broad. Only call a rack "nearby" when it is
        # within a short walk of the TourAPI coordinate.
        stations = [
            station for station in stations if station.get("distance_m", 10_000) <= 1_200
        ]
        stations.sort(key=lambda station: station.get("distance_m", 10_000))

    updated_at = _text(root, "PPLTN_TIME") or _text(root, "SBIKE_TIME")
    commercial_level = _text(root, "AREA_CMRCL_LVL")
    return {
        "available": bool(level or stations or commercial_level),
        "configured": True,
        "mapped": True,
        "area_name": _text(root, "AREA_NM") or requested_area,
        "area_code": _text(root, "AREA_CD") or requested_code,
        "congestion": {
            "level": level or "정보 없음",
            "emoji": CONGESTION_EMOJI.get(level, "⚪"),
            "message": _text(root, "AREA_CONGEST_MSG"),
            "population_min": population_min,
            "population_max": population_max,
            "updated_at": updated_at,
        },
        "bike": {
            "available_count": sum(item["available_count"] for item in stations),
            "station_count": len(stations),
            "radius_m": 1_200 if distance_filter_applied else None,
            "stations": stations[:3],
        },
        "commercial": {
            "available": bool(commercial_level),
            "level": commercial_level,
            "emoji": COMMERCIAL_EMOJI.get(commercial_level, "⚪"),
            "message": _text(root, "AREA_CMRCL_MSG"),
            "updated_at": _text(root, "CMRCL_TIME"),
        },
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": "서울 열린데이터광장",
    }


def _plain_text(value: object) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]*>", " ", unescape(str(value or "")))).strip()


def _official_web_json(opener, path: str, area_name: str) -> object:
    query = urlencode({"hotspotNm": area_name})
    request = Request(
        f"{_OFFICIAL_WEB_BASE}{path}?{query}",
        headers={
            "User-Agent": "SeoulMySoulMate/1.0",
            "Referer": f"{_OFFICIAL_WEB_BASE}/map",
            "Accept": "application/json, text/plain, */*",
        },
    )
    with opener.open(request, timeout=_OFFICIAL_WEB_TIMEOUT_SECONDS) as response:
        content_type = response.headers.get("Content-Type", "").lower()
        if "application/json" not in content_type:
            raise ValueError("서울시 공식 화면이 JSON 대신 다른 응답을 반환했습니다.")
        return json.loads(response.read().decode("utf-8"))


def _official_web_pair(opener, area_name: str) -> tuple[object, object]:
    with ThreadPoolExecutor(max_workers=2) as executor:
        population_future = executor.submit(
            _official_web_json, opener, "/api/ppltn", area_name
        )
        bike_future = executor.submit(
            _official_web_json, opener, "/api/bike", area_name
        )
        return population_future.result(), bike_future.result()


def _fetch_official_web_citydata(
    area: SeoulHotspot,
    longitude: float | None = None,
    latitude: float | None = None,
) -> dict:
    """Fallback to the official HTTPS screen when the documented API is unreachable.

    This is deliberately isolated from the primary Open API because the web
    endpoint is an internal implementation and can change without notice.
    """
    cookie_jar = CookieJar()
    opener = build_opener(HTTPCookieProcessor(cookie_jar))
    try:
        # The current deployment accepts a direct request with the official
        # Referer. If it starts requiring a session again, bootstrap one once.
        population_rows, bike_payload = _official_web_pair(opener, area.area_name)
    except (HTTPError, ValueError):
        map_request = Request(
            f"{_OFFICIAL_WEB_BASE}/map",
            headers={"User-Agent": "SeoulMySoulMate/1.0"},
        )
        with opener.open(map_request, timeout=_OFFICIAL_WEB_TIMEOUT_SECONDS) as response:
            response.read(1)
        population_rows, bike_payload = _official_web_pair(opener, area.area_name)
    population = (
        population_rows[0]
        if isinstance(population_rows, list) and population_rows
        else {}
    )
    if not isinstance(population, dict) or not isinstance(bike_payload, dict):
        raise ValueError("서울시 공식 화면의 실시간 응답 형식이 올바르지 않습니다.")

    level = str(population.get("congestion_text") or "").strip()
    message = _plain_text(population.get("congestion_instruction"))

    stations = []
    rows = bike_payload.get("row")
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, dict):
            continue
        name = str(row.get("sbike_spot_nm") or "").strip()
        if not name:
            continue
        station = {
            "name": name,
            "available_count": _number(row.get("sbike_parking_cnt")),
            "rack_count": _number(row.get("sbike_rack_cnt")),
            "longitude": row.get("sbike_x"),
            "latitude": row.get("sbike_y"),
        }
        station_longitude = _float(station["longitude"])
        station_latitude = _float(station["latitude"])
        if (
            longitude is not None
            and latitude is not None
            and station_longitude is not None
            and station_latitude is not None
        ):
            station["distance_m"] = _distance_metres(
                longitude, latitude, station_longitude, station_latitude
            )
        stations.append(station)

    distance_filter_applied = longitude is not None and latitude is not None and any(
        "distance_m" in station for station in stations
    )
    if distance_filter_applied:
        stations = [
            station for station in stations if station.get("distance_m", 10_000) <= 1_200
        ]
        stations.sort(key=lambda station: station.get("distance_m", 10_000))

    now = datetime.now(timezone.utc).isoformat()
    return {
        "available": bool(level or stations),
        "configured": True,
        "mapped": True,
        "area_name": str(population.get("hotspot_nm") or area.area_name),
        "area_code": area.area_code,
        "congestion": {
            "level": level or "정보 없음",
            "emoji": CONGESTION_EMOJI.get(level, "⚪"),
            "message": message,
            # The official screen fallback does not expose a reliable numeric
            # min/max range; only the documented Open API does.
            "population_min": 0,
            "population_max": 0,
            "updated_at": "",
        },
        "bike": {
            "available_count": sum(item["available_count"] for item in stations),
            "station_count": len(stations),
            "radius_m": 1_200 if distance_filter_applied else None,
            "stations": stations[:3],
        },
        "commercial": {
            "available": False,
            "level": "",
            "emoji": "⚪",
            "message": "",
            "updated_at": "",
        },
        "fetched_at": now,
        "source": "서울 실시간 도시데이터 공식 화면",
        "fallback": True,
        "notice": "공식 Open API 연결이 지연되어 서울시 공식 화면에서 수신했어요.",
    }


def _fetch_citydata(
    area: SeoulHotspot,
    api_key: str,
    longitude: float | None = None,
    latitude: float | None = None,
) -> dict:
    # AREA_CD from the supplied workbook avoids middot/parenthesis encoding
    # ambiguity. Integrated-only areas fall back to their exact AREA_NM.
    request_area = area.area_code or area.area_name
    encoded_area = quote(request_area, safe="")
    url = (
        f"http://openapi.seoul.go.kr:8088/{quote(api_key, safe='')}"
        f"/xml/citydata/1/30/{encoded_area}"
    )
    request = Request(url, headers={"User-Agent": "SeoulMySoulMate/1.0"})
    with urlopen(request, timeout=3) as response:  # noqa: S310 - fixed official host
        return _parse_citydata(
            response.read(),
            area.area_name,
            area.area_code,
            longitude=longitude,
            latitude=latitude,
        )


def _fetch_citydata_cmrcl(
    area: SeoulHotspot,
    api_key: str,
    longitude: float | None = None,
    latitude: float | None = None,
) -> dict:
    """The 상권 전용(citydata_cmrcl) service only serves AREA_NM, not AREA_CD,
    but has proven more reliable than the bundled ``citydata`` endpoint for
    several 발달상권 areas (e.g. 용리단길) whose integrated response is empty.
    """
    encoded_area = quote(area.area_name, safe="")
    url = (
        f"http://openapi.seoul.go.kr:8088/{quote(api_key, safe='')}"
        f"/xml/citydata_cmrcl/1/30/{encoded_area}"
    )
    request = Request(url, headers={"User-Agent": "SeoulMySoulMate/1.0"})
    with urlopen(request, timeout=3) as response:  # noqa: S310 - fixed official host
        return _parse_citydata(
            response.read(),
            area.area_name,
            area.area_code,
            longitude=longitude,
            latitude=latitude,
        )


def _fetch_area_payload(
    area: SeoulHotspot,
    api_key: str,
    longitude: float | None = None,
    latitude: float | None = None,
) -> dict:
    """Try the bundled endpoint first (richest fields), then the narrower
    상권 endpoint, which several areas answer even when the bundled one comes
    back empty. Raises if neither yields usable data (including a response
    that succeeds with no content), so callers can keep falling back to the
    web scrape and then the nearest other hotspot.
    """
    try:
        payload = _fetch_citydata(area, api_key, longitude, latitude)
        if payload.get("available"):
            return payload
        primary_error: Exception = ValueError(
            "서울시 통합 API가 이 지역의 데이터를 반환하지 않았습니다."
        )
    except Exception as error:  # noqa: BLE001 - retried below, never leaked
        primary_error = error

    try:
        cmrcl_payload = _fetch_citydata_cmrcl(area, api_key, longitude, latitude)
    except Exception as cmrcl_error:  # noqa: BLE001 - surfaced to caller
        raise primary_error from cmrcl_error

    if not cmrcl_payload.get("available"):
        raise primary_error
    return cmrcl_payload


def _fetch_area_payload_resilient(
    area: SeoulHotspot,
    api_key: str,
    longitude: float | None,
    latitude: float | None,
) -> dict:
    """Documented Open API first, then the official HTTPS screen. Nearest-area
    substitution needs the same resilience as the primary request path, or it
    fails outright whenever the documented API host is unreachable.
    """
    try:
        return _fetch_area_payload(area, api_key, longitude, latitude)
    except Exception as primary_error:  # noqa: BLE001 - web fallback tried next
        try:
            return _fetch_official_web_citydata(area, longitude, latitude)
        except Exception as web_error:
            raise primary_error from web_error


def _primary_in_backoff(now: float) -> bool:
    with _primary_health_lock:
        return now < _primary_retry_at


def _back_off_primary(now: float, error: Exception) -> None:
    if not isinstance(error, (TimeoutError, URLError, OSError)):
        return
    global _primary_retry_at
    with _primary_health_lock:
        _primary_retry_at = max(_primary_retry_at, now + _PRIMARY_BACKOFF_SECONDS)


def _failure_payload(area: SeoulHotspot, error: Exception) -> dict:
    timed_out = isinstance(error, TimeoutError) or (
        isinstance(error, URLError) and isinstance(error.reason, TimeoutError)
    )
    if timed_out:
        code = "upstream_timeout"
        reason = "서울시 실시간 서버 응답이 늦어지고 있어요. 잠시 후 다시 시도해 주세요."
        diagnostic = "개발 환경에서 openapi.seoul.go.kr:8088 연결 허용 여부를 확인해 주세요."
    elif isinstance(error, HTTPError):
        code = "upstream_http_error"
        reason = "서울시 실시간 서버가 요청을 처리하지 못했어요."
        diagnostic = "서울 열린데이터광장 서비스 상태를 확인해 주세요."
    elif isinstance(error, ValueError):
        code = "upstream_rejected"
        reason = "서울시 API가 이 지역의 데이터를 반환하지 않았어요."
        diagnostic = "인증키 권한과 citydata 서비스 신청 상태를 확인해 주세요."
    else:
        code = "upstream_unavailable"
        reason = "서울시 실시간 데이터에 잠시 연결할 수 없습니다."
        diagnostic = "백엔드 로그에서 오류 유형을 확인해 주세요."

    logger.warning(
        "Seoul citydata request failed area_code=%s error_type=%s",
        area.area_code or "name-only",
        type(error).__name__,
    )
    return {
        "available": False,
        "configured": True,
        "mapped": True,
        "area_name": area.area_name,
        "area_code": area.area_code,
        "error_code": code,
        "reason": reason,
        "diagnostic": diagnostic,
    }


_AREA_CENTROID_CACHE: dict[str, tuple[float, float]] | None = None
_area_centroid_lock = Lock()


def _area_centroids(db: Session) -> dict[str, tuple[float, float]]:
    """Average TourContent coordinates per hotspot, computed once per process.

    The 82-area workbook only lists names/codes, not coordinates, so this
    derives a usable centroid from data already loaded instead of keeping a
    second hardcoded location table in sync.
    """
    global _AREA_CENTROID_CACHE
    with _area_centroid_lock:
        if _AREA_CENTROID_CACHE is not None:
            return _AREA_CENTROID_CACHE

        totals: dict[str, list[float]] = {}
        counts: dict[str, int] = {}
        for content in db.execute(select(TourContent)).scalars():
            hotspot = map_content_to_hotspot(content)
            if not hotspot or not hotspot.area_code:
                continue
            longitude, latitude = _float(content.mapx), _float(content.mapy)
            if longitude is None or latitude is None:
                continue
            acc = totals.setdefault(hotspot.area_code, [0.0, 0.0])
            acc[0] += longitude
            acc[1] += latitude
            counts[hotspot.area_code] = counts.get(hotspot.area_code, 0) + 1

        _AREA_CENTROID_CACHE = {
            code: (values[0] / counts[code], values[1] / counts[code])
            for code, values in totals.items()
        }
        return _AREA_CENTROID_CACHE


def _nearest_hotspots(
    longitude: float,
    latitude: float,
    centroids: dict[str, tuple[float, float]],
    exclude_codes: set[str],
    limit: int = 2,
) -> list[SeoulHotspot]:
    scored = []
    for code, (area_longitude, area_latitude) in centroids.items():
        if code in exclude_codes:
            continue
        hotspot = HOTSPOTS_BY_CODE.get(code)
        if hotspot is None:
            continue
        distance = _distance_metres(longitude, latitude, area_longitude, area_latitude)
        scored.append((distance, hotspot))
    scored.sort(key=lambda item: item[0])
    return [hotspot for _, hotspot in scored[:limit]]


def _fetch_nearest_hotspot_payload(
    db: Session,
    area: SeoulHotspot,
    api_key: str,
    longitude: float | None,
    latitude: float | None,
) -> dict | None:
    """Substitute the closest other hotspot when the mapped area itself has
    no live data, so a visitor sees something relevant nearby instead of a
    bare failure message.
    """
    if longitude is None or latitude is None:
        return None

    centroids = _area_centroids(db)
    candidates = _nearest_hotspots(
        longitude, latitude, centroids, exclude_codes={area.area_code}
    )
    for candidate in candidates:
        try:
            payload = _fetch_area_payload_resilient(candidate, api_key, longitude, latitude)
        except Exception:  # noqa: BLE001 - try the next nearest candidate
            continue
        return {
            **payload,
            "fallback": True,
            "notice": (
                f"'{area.area_name}'의 실시간 데이터가 없어 "
                f"가장 가까운 관측 지역인 '{candidate.area_name}'의 정보를 보여드려요."
            ),
        }
    return None


@router.get("/areas")
def realtime_areas() -> dict:
    """Expose the exact workbook-backed subset for diagnostics and UI copy."""
    return {
        "total": len(SEOUL_HOTSPOTS),
        "source": "서울시 실시간 도시데이터 121개 관측지역 목록",
        "items": [
            {
                "category": area.category,
                "number": area.number,
                "area_code": area.area_code,
                "area_name": area.area_name,
            }
            for area in SEOUL_HOTSPOTS
        ],
    }


_AREAS_CONGESTION_CACHE_TTL_SECONDS = 180
_areas_congestion_cache: tuple[float, dict] | None = None
_areas_congestion_lock = Lock()


def _fetch_one_area_congestion(
    db: Session, area: SeoulHotspot, api_key: str
) -> dict | None:
    centroids = _area_centroids(db)
    center = centroids.get(area.area_code)
    if center is None:
        return None
    longitude, latitude = center
    try:
        payload = _fetch_area_payload_resilient(area, api_key, longitude, latitude)
    except Exception as error:  # noqa: BLE001 - this area is simply omitted
        logger.info(
            "Dashboard congestion fetch skipped area_code=%s error_type=%s",
            area.area_code,
            type(error).__name__,
        )
        return None
    if not payload.get("available"):
        return None
    return {
        "area_code": area.area_code,
        "area_name": area.area_name,
        "category": area.category,
        "longitude": longitude,
        "latitude": latitude,
        "congestion": payload["congestion"],
        "stale": bool(payload.get("stale")),
    }


def get_areas_congestion(db: Session, refresh: bool = False) -> dict:
    """Bulk congestion snapshot for the map dashboard.

    Only areas with a derivable centroid (at least one matching TourContent)
    are included, since the 121-area workbook lists names/codes only, not
    coordinates. Fetched in parallel and cached process-wide so opening the
    map dashboard does not re-query up to 121 areas on every request. Shared
    with ``geo.py`` so the district-level aggregation reuses this same cache
    instead of re-fetching every area a second time.
    """
    global _areas_congestion_cache

    now = monotonic()
    with _areas_congestion_lock:
        cached = _areas_congestion_cache
    if not refresh and cached and now - cached[0] < _AREAS_CONGESTION_CACHE_TTL_SECONDS:
        return {**cached[1], "cached": True}

    api_key = get_seoul_population_api_key()
    if not api_key:
        return {
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "configured": False,
            "items": [],
            "cached": False,
        }

    centroids = _area_centroids(db)
    areas = [area for area in SEOUL_HOTSPOTS if area.area_code in centroids]

    items: list[dict] = []
    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = {
            executor.submit(_fetch_one_area_congestion, db, area, api_key): area
            for area in areas
        }
        for future in futures:
            result = future.result()
            if result is not None:
                items.append(result)

    payload = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "configured": True,
        "total_areas": len(areas),
        "items": items,
    }
    with _areas_congestion_lock:
        _areas_congestion_cache = (now, payload)
    return {**payload, "cached": False}


@router.get("/areas/congestion")
def realtime_areas_congestion(
    refresh: bool = False,
    db: Session = Depends(get_db),
) -> dict:
    return get_areas_congestion(db, refresh)


@router.get("/contents/{contentid}")
def content_realtime(
    contentid: str,
    refresh: bool = False,
    db: Session = Depends(get_db),
) -> dict:
    content = db.scalar(
        select(TourContent).where(TourContent.contentid == contentid)
    )
    if content is None:
        return {
            "available": False,
            "configured": bool(get_seoul_citydata_api_key()),
            "mapped": False,
            "reason": "관광지 정보를 찾을 수 없습니다.",
        }

    api_key = get_seoul_citydata_api_key()

    area = map_content_to_hotspot(content)
    if not area:
        # Most TourContent titles do not literally match one of the 82
        # observed hotspots. Rather than give up, substitute the nearest of
        # those 82 areas by raw coordinate distance so a visitor still sees a
        # relevant live reading instead of a bare "not supported" message.
        if api_key:
            longitude, latitude = _float(content.mapx), _float(content.mapy)
            if longitude is not None and latitude is not None:
                centroids = _area_centroids(db)
                for candidate in _nearest_hotspots(
                    longitude, latitude, centroids, exclude_codes=set(), limit=3
                ):
                    try:
                        payload = _fetch_area_payload_resilient(
                            candidate, api_key, longitude, latitude
                        )
                    except Exception:  # noqa: BLE001 - try the next nearest candidate
                        continue
                    return {
                        **payload,
                        "fallback": True,
                        "notice": (
                            f"'{content.title}'은(는) 실시간 관측 지역이 아니어서 "
                            f"가장 가까운 관측 지역인 '{candidate.area_name}'의 정보를 보여드려요."
                        ),
                        "cached": False,
                    }
        return {
            "available": False,
            "configured": bool(api_key),
            "mapped": False,
            "reason": "서울시 주요 실시간 관측 지역과 정확히 매칭되지 않은 장소예요.",
            "supported_area_count": len(SEOUL_HOTSPOTS),
        }

    if not api_key:
        return {
            "available": False,
            "configured": False,
            "mapped": True,
            "area_name": area.area_name,
            "area_code": area.area_code,
            "reason": "서울시 실시간 도시데이터 키를 설정해 주세요.",
        }

    now = monotonic()
    # Bike stations are distance-filtered around the individual content, so
    # two places mapped to the same Seoul hotspot must not share a parsed cache.
    cache_key = f"{area.area_code or area.area_name}:{contentid}"
    with _cache_lock:
        cached = _cache.get(cache_key)
        failed = _error_cache.get(cache_key)
    if not refresh and cached and now - cached[0] < _CACHE_TTL_SECONDS:
        return {**cached[1], "cached": True}
    if not refresh and failed and now - failed[0] < _ERROR_CACHE_TTL_SECONDS:
        return {**failed[1], "cached": True}

    longitude, latitude = _float(content.mapx), _float(content.mapy)
    primary_skipped = _primary_in_backoff(now)
    try:
        if primary_skipped:
            raise TimeoutError("documented API is in a short connection backoff")
        payload = _fetch_area_payload(area, api_key, longitude, latitude)
    except Exception as primary_error:  # Never leak the URL or API key.
        if not primary_skipped:
            _back_off_primary(now, primary_error)
        try:
            payload = _fetch_official_web_citydata(area, longitude, latitude)
        except Exception as fallback_error:
            logger.warning(
                "Seoul official web fallback failed area_code=%s error_type=%s",
                area.area_code or "name-only",
                type(fallback_error).__name__,
            )
            if cached and now - cached[0] < _MAX_STALE_SECONDS:
                return {
                    **cached[1],
                    "cached": True,
                    "stale": True,
                    "notice": "실시간 갱신이 지연되어 마지막 정보를 보여드려요.",
                }

            nearest_payload = _fetch_nearest_hotspot_payload(
                db, area, api_key, longitude, latitude
            )
            if nearest_payload is not None:
                with _cache_lock:
                    _cache[cache_key] = (now, nearest_payload)
                    _error_cache.pop(cache_key, None)
                return {**nearest_payload, "cached": False}

            failure = _failure_payload(area, primary_error)
            with _cache_lock:
                _error_cache[cache_key] = (now, failure)
            return {**failure, "cached": False}

    with _cache_lock:
        _cache[cache_key] = (now, payload)
        _error_cache.pop(cache_key, None)
    return {**payload, "cached": False}
