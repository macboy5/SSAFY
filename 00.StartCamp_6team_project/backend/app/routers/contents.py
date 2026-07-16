from threading import Lock
from time import monotonic

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import Float, cast, func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Comment, Post, PostLike, TourContent
from ..schemas import ContentDetail, ContentListResponse, ContentMapResponse, PostSummary

router = APIRouter(prefix="/api/contents", tags=["contents"])

_MAP_CACHE_FRESH_SECONDS = 30 * 60
_MAP_CACHE_STALE_SECONDS = 24 * 60 * 60
_map_cache: tuple[float, ContentMapResponse] | None = None
_map_cache_lock = Lock()


@router.get("", response_model=ContentListResponse)
def list_contents(
    category: str | None = None,
    area: str | None = None,
    keyword: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
) -> ContentListResponse:
    query = select(TourContent)

    if category:
        query = query.where(TourContent.category == category)
    if area:
        query = query.where(TourContent.addr1.contains(area))
    if keyword:
        query = query.where(TourContent.title.contains(keyword))

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0

    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    rows = db.execute(
        query.order_by(TourContent.id).offset((page - 1) * page_size).limit(page_size)
    ).scalars().all()

    return ContentListResponse(total=total, page=page, page_size=page_size, items=rows)


def _load_map_contents(
    db: Session,
    category: str | None = None,
    area: str | None = None,
    keyword: str | None = None,
) -> ContentMapResponse:
    longitude = cast(TourContent.mapx, Float)
    latitude = cast(TourContent.mapy, Float)
    coordinate_filter = (
        (TourContent.mapx != "")
        & (TourContent.mapy != "")
        & longitude.between(126.7, 127.3)
        & latitude.between(37.4, 37.8)
    )
    query = select(TourContent).where(coordinate_filter)
    if category:
        query = query.where(TourContent.category == category)
    if area:
        query = query.where(TourContent.addr1.contains(area))
    if keyword:
        query = query.where(TourContent.title.contains(keyword))
    rows = db.execute(query.order_by(TourContent.title).limit(10000)).scalars().all()
    coordinate_total = db.scalar(
        select(func.count()).select_from(TourContent).where(
            TourContent.mapx != "", TourContent.mapy != ""
        )
    ) or 0
    valid_coordinate_total = db.scalar(
        select(func.count()).select_from(TourContent).where(coordinate_filter)
    ) or 0
    return ContentMapResponse(
        total=len(rows),
        excluded=max(coordinate_total - valid_coordinate_total, 0),
        items=rows,
    )


@router.get("/map", response_model=ContentMapResponse)
def map_contents(
    response: Response,
    category: str | None = None,
    area: str | None = None,
    keyword: str | None = None,
    db: Session = Depends(get_db),
) -> ContentMapResponse:
    global _map_cache

    cacheable = not any(value and value.strip() for value in (category, area, keyword))
    if not cacheable:
        response.headers["Cache-Control"] = "no-store"
        return _load_map_contents(db, category, area, keyword)

    response.headers["Cache-Control"] = (
        f"public, max-age={_MAP_CACHE_FRESH_SECONDS}, "
        f"stale-if-error={_MAP_CACHE_STALE_SECONDS}"
    )
    now = monotonic()
    with _map_cache_lock:
        if _map_cache is not None:
            cached_at, cached_response = _map_cache
            if now - cached_at < _MAP_CACHE_FRESH_SECONDS:
                return cached_response

        stale_response = None
        if _map_cache is not None and now - _map_cache[0] < _MAP_CACHE_STALE_SECONDS:
            stale_response = _map_cache[1]

        try:
            fresh_response = _load_map_contents(db)
        except Exception:
            if stale_response is not None:
                return stale_response
            raise

        _map_cache = (monotonic(), fresh_response)
        return fresh_response


@router.get("/{contentid}")
def get_content(contentid: str, db: Session = Depends(get_db)):
    content = db.execute(
        select(TourContent).where(TourContent.contentid == contentid)
    ).scalar_one_or_none()
    if content is None:
        raise HTTPException(status_code=404, detail="콘텐츠를 찾을 수 없습니다.")

    posts = db.execute(
        select(Post)
        .where(Post.content_id == contentid)
        .order_by(Post.created_at.desc())
        .limit(10)
    ).scalars().all()
    post_ids = [post.id for post in posts]
    like_counts = {}
    comment_counts = {}
    if post_ids:
        like_counts = dict(
            db.execute(
                select(PostLike.post_id, func.count(PostLike.user_id))
                .where(PostLike.post_id.in_(post_ids))
                .group_by(PostLike.post_id)
            ).all()
        )
        comment_counts = dict(
            db.execute(
                select(Comment.post_id, func.count(Comment.id))
                .where(Comment.post_id.in_(post_ids))
                .group_by(Comment.post_id)
            ).all()
        )

    return {
        "content": ContentDetail.model_validate(content),
        "posts": [
            PostSummary.model_validate(post).model_copy(
                update={
                    "like_count": like_counts.get(post.id, 0),
                    "comment_count": comment_counts.get(post.id, 0),
                }
            )
            for post in posts
        ],
    }
