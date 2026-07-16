from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, or_, select, union_all
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models import Comment, Post, PostCourseItem, PostLike, TourContent, User
from ..schemas import (
    CommentCreate,
    CommentOut,
    CommunityPlaceSummary,
    ContentSummary,
    CourseItemOut,
    LikeState,
    PostCreate,
    PostDetailOut,
    PostListResponse,
    PostSummary,
    PostUpdate,
)
from .auth import get_current_user, get_optional_user

router = APIRouter(prefix="/api", tags=["community"])


def _get_post_or_404(db: Session, post_id: int) -> Post:
    post = db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    return post


def _require_post_owner(post: Post, user: User) -> None:
    # Legacy rows intentionally remain readable but are not assigned to an
    # arbitrary new account.
    if post.author_id is None or post.author_id != user.id:
        raise HTTPException(status_code=403, detail="작성자만 변경할 수 있습니다.")


def _comment_out(comment: Comment, user: User | None) -> CommentOut:
    return CommentOut(
        id=comment.id,
        body=comment.body,
        nickname=comment.nickname,
        created_at=comment.created_at,
        author_id=comment.author_id,
        is_owner=user is not None and comment.author_id == user.id,
    )


def _post_summary(
    post: Post,
    user: User | None,
    like_count: int = 0,
    comment_count: int = 0,
    liked_by_me: bool = False,
) -> PostSummary:
    return PostSummary(
        id=post.id,
        title=post.title,
        body=post.body,
        nickname=post.nickname,
        author_id=post.author_id,
        content_id=post.content_id,
        created_at=post.created_at,
        content=(
            ContentSummary.model_validate(post.content) if post.content else None
        ),
        post_type=post.post_type or "review",
        travel_date=post.travel_date,
        course_items=[
            CourseItemOut(
                sort_order=item.sort_order,
                content=ContentSummary.model_validate(item.content),
            )
            for item in sorted(post.course_items, key=lambda item: item.sort_order)
            if item.content is not None
        ],
        like_count=like_count,
        comment_count=comment_count,
        liked_by_me=liked_by_me,
        is_owner=user is not None and post.author_id == user.id,
    )


def _social_states(
    db: Session, posts: list[Post], user: User | None
) -> tuple[dict[int, int], dict[int, int], set[int]]:
    post_ids = [post.id for post in posts]
    if not post_ids:
        return {}, {}, set()

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
    liked_ids: set[int] = set()
    if user is not None:
        liked_ids = set(
            db.scalars(
                select(PostLike.post_id).where(
                    PostLike.user_id == user.id, PostLike.post_id.in_(post_ids)
                )
            ).all()
        )
    return like_counts, comment_counts, liked_ids


def _like_state(db: Session, post_id: int, user: User) -> LikeState:
    count = db.scalar(
        select(func.count()).select_from(PostLike).where(PostLike.post_id == post_id)
    ) or 0
    liked = db.get(PostLike, (user.id, post_id)) is not None
    return LikeState(like_count=count, liked_by_me=liked)


def _validate_course_contents(db: Session, content_ids: list[str]) -> list[str]:
    if len(content_ids) < 2:
        raise HTTPException(status_code=422, detail="여행 코스에는 장소를 두 곳 이상 담아 주세요.")
    if len(content_ids) > 10:
        raise HTTPException(status_code=422, detail="한 코스에는 장소를 최대 열 곳까지 담을 수 있습니다.")
    if len(set(content_ids)) != len(content_ids):
        raise HTTPException(status_code=422, detail="여행 코스에 같은 장소를 두 번 담을 수 없습니다.")

    found_ids = set(
        db.scalars(
            select(TourContent.contentid).where(TourContent.contentid.in_(content_ids))
        ).all()
    )
    missing = [content_id for content_id in content_ids if content_id not in found_ids]
    if missing:
        raise HTTPException(status_code=404, detail="코스에 담긴 장소 중 찾을 수 없는 곳이 있습니다.")
    return content_ids


@router.get("/posts", response_model=PostListResponse)
def list_posts(
    content_id: str | None = None,
    category: str | None = None,
    keyword: str | None = None,
    post_type: Literal["review", "course"] | None = None,
    sort: Literal["newest", "likes", "comments"] = "newest",
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
) -> PostListResponse:
    query = select(Post).options(
        joinedload(Post.content),
        joinedload(Post.course_items).joinedload(PostCourseItem.content),
    ).outerjoin(
        TourContent, Post.content_id == TourContent.contentid
    )
    if content_id:
        query = query.where(
            or_(
                Post.content_id == content_id,
                Post.course_items.any(PostCourseItem.content_id == content_id),
            )
        )
    if category:
        query = query.where(
            or_(
                TourContent.category == category,
                Post.course_items.any(
                    PostCourseItem.content.has(TourContent.category == category)
                ),
            )
        )
    if post_type:
        query = query.where(Post.post_type == post_type)
    if keyword:
        query = query.where(
            or_(
                Post.title.contains(keyword),
                Post.body.contains(keyword),
                TourContent.title.contains(keyword),
                TourContent.addr1.contains(keyword),
                Post.course_items.any(
                    PostCourseItem.content.has(
                        or_(
                            TourContent.title.contains(keyword),
                            TourContent.addr1.contains(keyword),
                        )
                    )
                ),
            )
        )

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    like_count_order = (
        select(func.count())
        .select_from(PostLike)
        .where(PostLike.post_id == Post.id)
        .correlate(Post)
        .scalar_subquery()
    )
    comment_count_order = (
        select(func.count())
        .select_from(Comment)
        .where(Comment.post_id == Post.id)
        .correlate(Post)
        .scalar_subquery()
    )
    if sort == "likes":
        order_by = (like_count_order.desc(), Post.created_at.desc(), Post.id.desc())
    elif sort == "comments":
        order_by = (comment_count_order.desc(), Post.created_at.desc(), Post.id.desc())
    else:
        order_by = (Post.created_at.desc(), Post.id.desc())

    posts = db.execute(
        query.order_by(*order_by)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).unique().scalars().all()
    like_counts, comment_counts, liked_ids = _social_states(db, posts, user)

    return PostListResponse(
        total=total,
        page=page,
        page_size=page_size,
        sort=sort,
        items=[
            _post_summary(
                post,
                user,
                like_counts.get(post.id, 0),
                comment_counts.get(post.id, 0),
                post.id in liked_ids,
            )
            for post in posts
        ],
    )


@router.get("/community/places", response_model=list[CommunityPlaceSummary])
def popular_community_places(limit: int = 8, db: Session = Depends(get_db)):
    limit = min(max(limit, 1), 20)
    place_posts = union_all(
        select(Post.id.label("post_id"), Post.content_id.label("content_id")).where(
            Post.post_type != "course", Post.content_id.is_not(None)
        ),
        select(
            PostCourseItem.post_id.label("post_id"),
            PostCourseItem.content_id.label("content_id"),
        ),
    ).subquery()
    post_count = func.count(func.distinct(place_posts.c.post_id))
    rows = db.execute(
        select(TourContent, post_count.label("post_count"))
        .join(place_posts, place_posts.c.content_id == TourContent.contentid)
        .group_by(TourContent.id)
        .order_by(post_count.desc(), TourContent.title)
        .limit(limit)
    ).all()
    return [
        CommunityPlaceSummary(
            content=ContentSummary.model_validate(content), post_count=count
        )
        for content, count in rows
    ]


@router.post("/posts", response_model=PostSummary, status_code=201)
def create_post(
    payload: PostCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PostSummary:
    if payload.post_type == "course":
        course_content_ids = _validate_course_contents(db, payload.course_content_ids)
        content_id = course_content_ids[0]
    else:
        course_content_ids = []
        content_id = payload.content_id
        if not db.scalar(
            select(TourContent).where(TourContent.contentid == content_id)
        ):
            raise HTTPException(status_code=404, detail="연결할 장소를 찾을 수 없습니다.")

    post = Post(
        title=payload.title,
        body=payload.body,
        nickname=user.nickname,
        password_hash="",
        author_id=user.id,
        content_id=content_id,
        post_type=payload.post_type,
        travel_date=payload.travel_date if payload.post_type == "course" else None,
    )
    db.add(post)
    db.flush()
    for sort_order, course_content_id in enumerate(course_content_ids):
        post.course_items.append(
            PostCourseItem(content_id=course_content_id, sort_order=sort_order)
        )
    db.commit()
    post = db.execute(
        select(Post)
        .options(
            joinedload(Post.content),
            joinedload(Post.course_items).joinedload(PostCourseItem.content),
        )
        .where(Post.id == post.id)
    ).unique().scalar_one()
    return _post_summary(post, user)


@router.get("/posts/{post_id}", response_model=PostDetailOut)
def get_post(
    post_id: int,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
) -> PostDetailOut:
    post = db.execute(
        select(Post)
        .options(
            joinedload(Post.comments),
            joinedload(Post.content),
            joinedload(Post.course_items).joinedload(PostCourseItem.content),
        )
        .where(Post.id == post_id)
    ).unique().scalar_one_or_none()
    if post is None:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")

    like_counts, comment_counts, liked_ids = _social_states(db, [post], user)
    summary = _post_summary(
        post,
        user,
        like_counts.get(post.id, 0),
        comment_counts.get(post.id, 0),
        post.id in liked_ids,
    )
    return PostDetailOut(
        **summary.model_dump(),
        updated_at=post.updated_at,
        comments=[
            _comment_out(comment, user)
            for comment in sorted(post.comments, key=lambda item: (item.created_at, item.id))
        ],
    )


@router.put("/posts/{post_id}", response_model=PostSummary)
def update_post(
    post_id: int,
    payload: PostUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PostSummary:
    post = _get_post_or_404(db, post_id)
    _require_post_owner(post, user)
    post.title = payload.title
    post.body = payload.body
    if post.post_type == "course":
        if payload.travel_date is not None:
            post.travel_date = payload.travel_date
        if payload.course_content_ids is not None:
            course_content_ids = _validate_course_contents(db, payload.course_content_ids)
            post.course_items.clear()
            db.flush()
            for sort_order, content_id in enumerate(course_content_ids):
                post.course_items.append(
                    PostCourseItem(content_id=content_id, sort_order=sort_order)
                )
            post.content_id = course_content_ids[0]
    db.commit()
    post = db.execute(
        select(Post)
        .options(
            joinedload(Post.content),
            joinedload(Post.course_items).joinedload(PostCourseItem.content),
        )
        .where(Post.id == post.id)
    ).unique().scalar_one()
    state = _like_state(db, post.id, user)
    comment_count = db.scalar(
        select(func.count()).select_from(Comment).where(Comment.post_id == post.id)
    ) or 0
    return _post_summary(
        post, user, state.like_count, comment_count, state.liked_by_me
    )


@router.delete("/posts/{post_id}", status_code=204)
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    post = _get_post_or_404(db, post_id)
    _require_post_owner(post, user)
    db.delete(post)
    db.commit()


@router.post("/posts/{post_id}/comments", response_model=CommentOut, status_code=201)
def create_comment(
    post_id: int,
    payload: CommentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CommentOut:
    _get_post_or_404(db, post_id)
    comment = Comment(
        post_id=post_id,
        body=payload.body,
        nickname=user.nickname,
        password_hash="",
        author_id=user.id,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return _comment_out(comment, user)


@router.delete("/comments/{comment_id}", status_code=204)
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    comment = db.get(Comment, comment_id)
    if comment is None:
        raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다.")
    if comment.author_id is None or comment.author_id != user.id:
        raise HTTPException(status_code=403, detail="작성자만 삭제할 수 있습니다.")
    db.delete(comment)
    db.commit()


@router.put("/posts/{post_id}/like", response_model=LikeState)
def like_post(
    post_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> LikeState:
    _get_post_or_404(db, post_id)
    if db.get(PostLike, (user.id, post_id)) is None:
        db.add(PostLike(user_id=user.id, post_id=post_id))
        try:
            db.commit()
        except IntegrityError:
            # A simultaneous duplicate PUT still has the requested end state.
            db.rollback()
    return _like_state(db, post_id, user)


@router.delete("/posts/{post_id}/like", response_model=LikeState)
def unlike_post(
    post_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> LikeState:
    _get_post_or_404(db, post_id)
    like = db.get(PostLike, (user.id, post_id))
    if like is not None:
        db.delete(like)
        db.commit()
    return _like_state(db, post_id, user)
