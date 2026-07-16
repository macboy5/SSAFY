from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ContentSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    contentid: str
    category: str
    title: str
    addr1: str
    firstimage: str
    mapx: str
    mapy: str


class ContentDetail(ContentSummary):
    addr2: str
    tel: str
    firstimage2: str
    areacode: str
    cat1: str
    cat2: str
    cat3: str


class ContentListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ContentSummary]


class ContentMapResponse(BaseModel):
    total: int
    excluded: int = 0
    items: list[ContentSummary]


class SignUpRequest(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    nickname: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        value = value.strip().lower()
        local, separator, domain = value.partition("@")
        if not separator or not local or "." not in domain or domain.startswith("."):
            raise ValueError("올바른 이메일 주소를 입력해 주세요.")
        return value

    @field_validator("nickname")
    @classmethod
    def validate_nickname(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("닉네임을 입력해 주세요.")
        return value


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=1, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    nickname: str
    created_at: datetime


class AuthResponse(BaseModel):
    # token is the app-facing field; access_token keeps the response compatible
    # with conventional OAuth-style clients.
    token: str
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_at: datetime
    user: UserOut


class CommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=1000)


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    body: str
    nickname: str
    created_at: datetime
    author_id: int | None = None
    is_owner: bool = False


class PostCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    body: str = Field(min_length=1, max_length=12000)
    content_id: str | None = Field(default=None, min_length=1, max_length=32)
    post_type: Literal["review", "course"] = "review"
    travel_date: date | None = None
    course_content_ids: list[str] = Field(default_factory=list, max_length=10)

    @model_validator(mode="after")
    def validate_places(self):
        if self.post_type == "course":
            if self.travel_date is None:
                raise ValueError("여행한 날짜를 선택해 주세요.")
            if self.travel_date >= date.today():
                raise ValueError("여행을 마친 다음 날부터 하루 코스를 기록할 수 있어요.")
            if len(self.course_content_ids) < 2:
                raise ValueError("여행 코스에는 장소를 두 곳 이상 담아 주세요.")
            if len(set(self.course_content_ids)) != len(self.course_content_ids):
                raise ValueError("여행 코스에 같은 장소를 두 번 담을 수 없습니다.")
        elif not self.content_id:
            raise ValueError("후기를 남길 장소를 선택해 주세요.")
        return self


class PostUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    body: str = Field(min_length=1, max_length=12000)
    travel_date: date | None = None
    course_content_ids: list[str] | None = Field(default=None, max_length=10)

    @model_validator(mode="after")
    def validate_course_changes(self):
        if self.travel_date is not None and self.travel_date >= date.today():
            raise ValueError("여행을 마친 다음 날부터 하루 코스를 기록할 수 있어요.")
        if self.course_content_ids is not None:
            if len(self.course_content_ids) < 2:
                raise ValueError("여행 코스에는 장소를 두 곳 이상 담아 주세요.")
            if len(set(self.course_content_ids)) != len(self.course_content_ids):
                raise ValueError("여행 코스에 같은 장소를 두 번 담을 수 없습니다.")
        return self


class CourseItemOut(BaseModel):
    sort_order: int
    content: ContentSummary


class PostSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    body: str
    nickname: str
    author_id: int | None = None
    content_id: str | None
    created_at: datetime
    content: ContentSummary | None = None
    post_type: Literal["review", "course"] = "review"
    travel_date: date | None = None
    course_items: list[CourseItemOut] = Field(default_factory=list)
    like_count: int = 0
    comment_count: int = 0
    liked_by_me: bool = False
    is_owner: bool = False


class PostDetailOut(PostSummary):
    updated_at: datetime
    comments: list[CommentOut] = Field(default_factory=list)


class PostListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    sort: Literal["newest", "likes", "comments"] = "newest"
    items: list[PostSummary]


class LikeState(BaseModel):
    like_count: int
    liked_by_me: bool


class CommunityPlaceSummary(BaseModel):
    content: ContentSummary
    post_count: int


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    history: list[ChatMessage] = Field(default_factory=list, max_length=20)
    context_ids: list[str] = Field(default_factory=list, max_length=10)


class ChatResponse(BaseModel):
    answer: str
    items: list[ContentSummary]
    mode: Literal["openai", "search"]


class ChatStatus(BaseModel):
    configured: bool
    mode: Literal["openai", "search"]
    model: str


class PlannerItemCreate(BaseModel):
    content_id: str
    plan_date: date
    visit_time: str = Field(default="", max_length=5)
    memo: str = Field(default="", max_length=500)


class PlannerItemUpdate(BaseModel):
    plan_date: date | None = None
    visit_time: str | None = Field(default=None, max_length=5)
    memo: str | None = Field(default=None, max_length=500)
    sort_order: int | None = None


class PlannerItemOut(BaseModel):
    id: int
    content_id: str
    plan_date: date
    visit_time: str
    memo: str
    sort_order: int
    content: ContentSummary
