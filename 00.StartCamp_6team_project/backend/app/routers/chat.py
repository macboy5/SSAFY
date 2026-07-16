import json
import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..config import get_openai_settings
from ..database import get_db
from ..models import TourContent, User
from ..schemas import ChatRequest, ChatResponse, ChatStatus, ContentSummary
from .auth import get_current_user

router = APIRouter(prefix="/api/chat", tags=["chat"])

CATEGORY_KEYWORDS = {
    "관광지": ["관광지", "명소", "공원", "산책", "야경"],
    "레포츠": ["레포츠", "액티비티", "스포츠", "운동", "체험"],
    "문화시설": ["문화시설", "박물관", "미술관", "전시", "갤러리"],
    "쇼핑": ["쇼핑", "시장", "백화점", "기념품"],
    "숙박": ["숙박", "호텔", "숙소", "펜션", "게스트하우스"],
    "여행코스": ["여행코스", "관광코스", "추천루트"],
    "축제공연행사": ["축제", "공연", "행사", "페스티벌", "콘서트"],
}
DISTRICTS = [
    "강남", "강동", "강북", "강서", "관악", "광진", "구로", "금천", "노원",
    "도봉", "동대문", "동작", "마포", "서대문", "서초", "성동", "성북", "송파",
    "양천", "영등포", "용산", "은평", "종로", "중구", "중랑",
]
STOP_WORDS = {
    "서울", "여행", "추천", "추천해줘", "알려줘", "보여줘", "근처", "주변", "장소",
    "곳", "가고", "싶어", "하고", "하루", "반나절", "시간", "코스", "일정",
}
GENERIC_CATEGORY_WORDS = set(CATEGORY_KEYWORDS) | {"관광", "코스"}
TOKEN_SYNONYMS = {"아이": ["아이", "어린이", "키즈", "가족"]}
FOLLOWUP_WORDS = ("그중", "그 중", "첫 번째", "첫번째", "두 번째", "두번째", "세 번째", "세번째", "그럼", "줄여", "늘려", "거기", "앞의")
_TOKEN_RE = re.compile(r"[가-힣A-Za-z0-9]+")


def _detect_category(message: str) -> str | None:
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in message for keyword in keywords):
            return category
    return None


def _detect_district(message: str) -> str | None:
    return next((district for district in DISTRICTS if district in message), None)


def _result_limit(message: str) -> int:
    if "반나절" in message:
        return 3
    if "하루" in message or "당일" in message:
        return 5
    if "1박" in message or "이틀" in message:
        return 6
    hours = re.search(r"(\d{1,2})\s*시간", message)
    return min(max(int(hours.group(1)), 2), 6) if hours else 5


def _meaningful_tokens(message: str) -> list[str]:
    normalized = []
    for raw_token in _TOKEN_RE.findall(message):
        token = raw_token
        for suffix in ("에서", "으로", "이랑", "에게", "하고", "근처", "주변", "와", "과", "은", "는", "이", "가", "을", "를", "에"):
            if token.endswith(suffix) and len(token) - len(suffix) >= 2:
                token = token[:-len(suffix)]
                break
        if (
            len(token) >= 2
            and token not in STOP_WORDS
            and token not in GENERIC_CATEGORY_WORDS
            and token not in DISTRICTS
            and not token.isdigit()
        ):
            normalized.extend(TOKEN_SYNONYMS.get(token, [token]))
    return list(dict.fromkeys(normalized))[:6]


def _run_search(
    db: Session,
    *,
    category: str | None,
    district: str | None,
    tokens: list[str],
    limit: int,
) -> list[TourContent]:
    query = select(TourContent)
    if category:
        query = query.where(TourContent.category == category)
    if district:
        query = query.where(TourContent.addr1.contains(district))
    if tokens:
        query = query.where(or_(*[
            or_(TourContent.title.contains(token), TourContent.addr1.contains(token))
            for token in tokens
        ]))
    candidates = db.execute(
        query.order_by(TourContent.title).limit(max(limit * 12, 60))
    ).scalars().all()

    def relevance(item: TourContent) -> tuple[int, int, str]:
        title_score = sum(token.lower() in item.title.lower() for token in tokens)
        address_score = sum(token.lower() in item.addr1.lower() for token in tokens)
        return (-(title_score * 4 + address_score), -int(bool(item.firstimage)), item.title)

    ranked = sorted(candidates, key=relevance)
    if category:
        return ranked[:limit]

    # A requested "course" benefits from a mix instead of many shops at one address.
    diverse: list[TourContent] = []
    used_categories: set[str] = set()
    for item in ranked:
        if item.category not in used_categories:
            diverse.append(item)
            used_categories.add(item.category)
        if len(diverse) == limit:
            return diverse
    for item in ranked:
        if item not in diverse:
            diverse.append(item)
        if len(diverse) == limit:
            break
    return diverse


def _search_contents(db: Session, message: str) -> list[TourContent]:
    category = _detect_category(message)
    district = _detect_district(message)
    tokens = _meaningful_tokens(message)
    limit = _result_limit(message)

    if not any((category, district, tokens)):
        return []
    return _run_search(
        db, category=category, district=district, tokens=tokens, limit=limit
    )


def _is_followup(message: str) -> bool:
    return any(word in message for word in FOLLOWUP_WORDS)


def _context_contents(
    db: Session, context_ids: list[str], message: str
) -> list[TourContent]:
    if not context_ids or not _is_followup(message):
        return []
    rows = db.execute(
        select(TourContent).where(TourContent.contentid.in_(context_ids))
    ).scalars().all()
    by_id = {item.contentid: item for item in rows}
    ordered = [by_id[item_id] for item_id in context_ids if item_id in by_id]
    if "첫 번째" in message or "첫번째" in message:
        return ordered[:1]
    if "두 번째" in message or "두번째" in message:
        return ordered[1:2]
    if "세 번째" in message or "세번째" in message:
        return ordered[2:3]
    return ordered[:_result_limit(message)]


def _fallback_answer(results: list[TourContent], message: str) -> str:
    if not results:
        return (
            "조건에 맞는 서울 관광정보를 찾지 못했어요. "
            "예: ‘마포에서 반나절 동안 갈 문화시설’처럼 지역, 관심 분야, 시간을 알려주세요."
        )
    lines = [f"• {item.title} — {item.addr1 or '주소 정보 없음'}" for item in results[:4]]
    time_note = " 요청하신 여행시간에 맞춰 카드 수를 조정했어요." if re.search(r"반나절|하루|당일|\d+\s*시간", message) else ""
    return "여행 조건에 잘 맞는 서울의 장소를 찾았어요." + time_note + "\n" + "\n".join(lines)


def _call_openai(
    *,
    api_key: str,
    model: str,
    message: str,
    history: list[dict[str, str]],
    results: list[TourContent],
) -> str:
    from openai import (
        APIConnectionError,
        APITimeoutError,
        AuthenticationError,
        OpenAI,
        OpenAIError,
        RateLimitError,
    )

    context_items = [
        {
            "contentid": item.contentid,
            "title": item.title,
            "category": item.category,
            "address": item.addr1,
        }
        for item in results
    ]
    instructions = (
        "너는 SeoulMySoulMate의 서울 여행 큐레이터다. 반드시 search_results에 포함된 장소만 "
        "추천하고 장소명과 주소를 원문 그대로 사용한다. 검색 결과에 없는 장소, 운영시간, 가격, "
        "이동시간을 만들어내지 않는다. 사용자의 지역·관심분야·여행시간을 반영해 한국어로 간결하게 "
        "설명한다. 결과가 비어 있거나 조건이 불충분하면 필요한 조건 한 가지만 다시 질문한다. "
        f"search_results={json.dumps(context_items, ensure_ascii=False)}"
    )
    input_messages = history[-10:] + [{"role": "user", "content": message}]
    try:
        response = OpenAI(api_key=api_key, timeout=25.0, max_retries=1).responses.create(
            model=model,
            instructions=instructions,
            input=input_messages,
            max_output_tokens=1200,
            store=False,
        )
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=502,
            detail="OpenAI 인증에 실패했습니다. 서버의 API 키를 확인해 주세요.",
        ) from exc
    except RateLimitError as exc:
        raise HTTPException(
            status_code=429,
            detail="AI 요청 한도에 도달했습니다. 잠시 후 다시 시도해 주세요.",
        ) from exc
    except APITimeoutError as exc:
        raise HTTPException(
            status_code=504,
            detail="AI 응답이 지연되고 있습니다. 잠시 후 다시 시도해 주세요.",
        ) from exc
    except APIConnectionError as exc:
        raise HTTPException(
            status_code=502,
            detail="OpenAI 서버에 연결하지 못했습니다. 잠시 후 다시 시도해 주세요.",
        ) from exc
    except OpenAIError as exc:
        raise HTTPException(
            status_code=502,
            detail="OpenAI 연결에 실패했습니다. backend/.env의 키와 모델명을 확인해 주세요.",
        ) from exc
    if getattr(response, "status", "completed") != "completed":
        raise HTTPException(
            status_code=502,
            detail="OpenAI 응답이 완료되지 않았습니다. 질문을 줄여 다시 시도해 주세요.",
        )
    answer = (response.output_text or "").strip()
    if not answer:
        raise HTTPException(
            status_code=502,
            detail="OpenAI가 빈 답변을 반환했습니다. 잠시 후 다시 시도해 주세요.",
        )
    return answer


@router.get("/status", response_model=ChatStatus)
def chat_status() -> ChatStatus:
    api_key, model = get_openai_settings()
    return ChatStatus(configured=bool(api_key), mode="openai" if api_key else "search", model=model)


@router.post("", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> ChatResponse:
    results = _context_contents(db, payload.context_ids, payload.message)
    if not results:
        results = _search_contents(db, payload.message)
    api_key, model = get_openai_settings()
    if api_key:
        history = [{"role": item.role, "content": item.content} for item in payload.history]
        answer = _call_openai(
            api_key=api_key,
            model=model,
            message=payload.message,
            history=history,
            results=results,
        )
        mode = "openai"
    else:
        answer = _fallback_answer(results, payload.message)
        mode = "search"
    return ChatResponse(
        answer=answer,
        items=[ContentSummary.model_validate(item) for item in results],
        mode=mode,
    )
