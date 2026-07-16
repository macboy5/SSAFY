# SeoulMySoulMate

서울 관광정보 7종(관광지·레포츠·문화시설·쇼핑·숙박·여행코스·축제공연행사)을 통합 제공하고, 익명 커뮤니티·데이터 기반 챗봇·여행코스 플래너를 제공하는 Vue3 + FastAPI + SQLite 서비스.

## Structure

- `backend/` - FastAPI + SQLAlchemy + SQLite
- `frontend/` - Vue 3 + Vite (Vue Router, Pinia)
- `data/` - 서울 관광정보 원본 JSON과 데이터 스키마·출처 문서
- `data/서울_*.json` - 서울 관광정보 원본 데이터(공공데이터, TourAPI 형식)
- `data/SCHEMA.md`, `data/SOURCE.md` - 원본 데이터 스키마와 출처·라이선스

## Backend

사전 준비: Python 3.11+

**최초 1회 설정**

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # OPENAI_API_KEY 입력 (미입력 시 챗봇은 키워드 기반 폴백 답변 사용)
```

**서버 실행 (이후 계속 이 명령만 사용)**

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- 최초 기동 시 `data/서울_*.json` 7종을 자동으로 SQLite(`app.db`)에 적재합니다. 이후에는 이미 적재된 데이터를 건너뜁니다.
- 데이터를 수동으로 재적재하려면: `python scripts/seed.py`
- 정상 기동 확인: 브라우저 또는 `curl http://localhost:8000/api/health` → `{"status":"ok"}`
- 종료: 터미널에서 `Ctrl+C`

## Frontend

사전 준비: Node.js 18+

**최초 1회 설정**

```bash
cd frontend
npm install
```

**개발 서버 실행 (이후 계속 이 명령만 사용)**

```bash
cd frontend
npm run dev
```

- 브라우저에서 `http://localhost:5173` 접속 (백엔드가 8000번 포트에서 먼저 켜져 있어야 `/api` 요청이 정상 동작합니다)
- 종료: 터미널에서 `Ctrl+C`

## API

- `GET /api/health`
- `GET /api/contents`, `GET /api/contents/{contentid}`
- `GET/POST /api/posts`, `GET/PUT/DELETE /api/posts/{id}`
- `POST /api/posts/{id}/comments`, `DELETE /api/comments/{id}`
- `POST /api/chat`
- `GET /api/chat/status`
- `GET/POST /api/planner`, `PATCH/DELETE /api/planner/{id}`
- `GET /api/contents/map`, `GET /api/community/places`

상세 기능과 완료 조건은 [`FEATURE_REQUIREMENTS.md`](FEATURE_REQUIREMENTS.md)에 정리되어 있습니다.

## Soul Chat OpenAI 설정

OpenAI 키는 브라우저에 노출되는 `frontend/.env`가 아니라 `backend/.env`에 저장합니다.

```env
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini
```

백엔드가 실행 중이어도 `.env`에 키를 저장한 다음 채팅 요청부터 자동으로 인식합니다. 키가 없으면 Soul Chat은 SQLite 검색 모드로 계속 동작합니다. 화면의 상태 새로고침 버튼 또는 `GET /api/chat/status`로 현재 모드를 확인할 수 있습니다.

## 카카오맵 설정

`frontend/.env.example`을 `frontend/.env`로 복사하고 카카오 개발자 콘솔의 JavaScript 키를 입력합니다.

```env
VITE_KAKAO_MAP_KEY=your_javascript_key
```

카카오 개발자 콘솔에서 아래 설정도 필요합니다.

1. **카카오맵 > 사용 설정**을 ON으로 변경합니다.
2. **앱 > 플랫폼 키 > JavaScript 키 > JavaScript SDK 도메인**에 `http://localhost:5173`을 등록합니다.
3. REST API 키가 아닌 **JavaScript 키**를 `.env`에 입력합니다.
4. 환경변수 변경 후 Vite 개발 서버를 완전히 종료하고 `npm run dev`로 다시 시작합니다.

키가 없거나 인증에 실패하면 지도 영역에 원인과 설정 방법이 표시되고 나머지 기능은 정상 동작합니다.

## 데이터 출처

서울 관광정보 7종 JSON은 한국관광공사 TourAPI 형식(지역기반목록조회)을 따르며, 서울 권역으로 필터링된 데이터입니다.
