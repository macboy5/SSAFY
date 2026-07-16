from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # The physical column name remains "username" so databases created during
    # the lightweight auth rollout stay compatible; the public identifier is email.
    email: Mapped[str] = mapped_column("username", String(254), unique=True, index=True)
    nickname: Mapped[str] = mapped_column(String(64))
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    sessions: Mapped[list["AuthSession"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    posts: Mapped[list["Post"]] = relationship(back_populates="author")
    comments: Mapped[list["Comment"]] = relationship(back_populates="author")
    likes: Mapped[list["PostLike"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    # The raw bearer token is returned once and is never persisted.
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)

    user: Mapped["User"] = relationship(back_populates="sessions")


class TourContent(Base):
    __tablename__ = "tour_contents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    contentid: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    contenttypeid: Mapped[str] = mapped_column(String(8), index=True)
    category: Mapped[str] = mapped_column(String(32), index=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    addr1: Mapped[str] = mapped_column(String(255), default="")
    addr2: Mapped[str] = mapped_column(String(255), default="")
    tel: Mapped[str] = mapped_column(String(64), default="")
    firstimage: Mapped[str] = mapped_column(String(512), default="")
    firstimage2: Mapped[str] = mapped_column(String(512), default="")
    mapx: Mapped[str] = mapped_column(String(32), default="")
    mapy: Mapped[str] = mapped_column(String(32), default="")
    areacode: Mapped[str] = mapped_column(String(16), default="", index=True)
    sigungucode: Mapped[str] = mapped_column(String(16), default="")
    cat1: Mapped[str] = mapped_column(String(16), default="")
    cat2: Mapped[str] = mapped_column(String(16), default="")
    cat3: Mapped[str] = mapped_column(String(16), default="")
    raw_json: Mapped[str] = mapped_column(Text, default="{}")

    posts: Mapped[list["Post"]] = relationship(back_populates="content")
    course_items: Mapped[list["PostCourseItem"]] = relationship(back_populates="content")


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    content_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("tour_contents.contentid"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text)
    # A review is tied to one place. A course post keeps its ordered stops in
    # post_course_items while content_id remains the first stop for backwards
    # compatibility with existing cards and place filters.
    post_type: Mapped[str] = mapped_column(String(16), default="review", index=True)
    travel_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    nickname: Mapped[str] = mapped_column(String(64), default="익명")
    # Kept for pre-account rows; account-owned rows store an empty sentinel.
    password_hash: Mapped[str] = mapped_column(String(255), default="")
    author_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    content: Mapped["TourContent | None"] = relationship(back_populates="posts")
    author: Mapped["User | None"] = relationship(back_populates="posts")
    comments: Mapped[list["Comment"]] = relationship(
        back_populates="post", cascade="all, delete-orphan"
    )
    likes: Mapped[list["PostLike"]] = relationship(
        back_populates="post", cascade="all, delete-orphan", passive_deletes=True
    )
    course_items: Mapped[list["PostCourseItem"]] = relationship(
        back_populates="post",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="PostCourseItem.sort_order",
    )


class PostCourseItem(Base):
    __tablename__ = "post_course_items"
    __table_args__ = (
        UniqueConstraint("post_id", "sort_order", name="uq_post_course_items_order"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("posts.id", ondelete="CASCADE"), index=True
    )
    content_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("tour_contents.contentid"), index=True
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    post: Mapped["Post"] = relationship(back_populates="course_items")
    content: Mapped["TourContent"] = relationship(back_populates="course_items")


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(Integer, ForeignKey("posts.id"), index=True)
    body: Mapped[str] = mapped_column(Text)
    nickname: Mapped[str] = mapped_column(String(64), default="익명")
    # Retained so existing SQLite tables can be migrated without a rebuild.
    password_hash: Mapped[str] = mapped_column(String(255), default="")
    author_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    post: Mapped["Post"] = relationship(back_populates="comments")
    author: Mapped["User | None"] = relationship(back_populates="comments")


class PostLike(Base):
    __tablename__ = "post_likes"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    post_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="likes")
    post: Mapped["Post"] = relationship(back_populates="likes")


class PlannerItem(Base):
    __tablename__ = "planner_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    client_id: Mapped[str] = mapped_column(String(64), index=True)
    content_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("tour_contents.contentid"), index=True
    )
    plan_date: Mapped[date] = mapped_column(Date, index=True)
    visit_time: Mapped[str] = mapped_column(String(5), default="")
    memo: Mapped[str] = mapped_column(String(500), default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    content: Mapped["TourContent"] = relationship()
