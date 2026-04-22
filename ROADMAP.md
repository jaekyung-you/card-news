# ROADMAP — Anthropic 뉴스 카드뉴스 자동화

Anthropic 뉴스를 매일 감지하여 한국어 카드뉴스를 생성, Instagram과 Slack에 자동 배포하는 파이프라인.

---

## 태스크 목록

### Phase 1 — 기반 세팅

- [x] **Task 1: 프로젝트 초기화**
  - 디렉토리 구조(`src/`, `templates/`, `output/`, `state/`, `.github/workflows/`) 생성
  - `requirements.txt`, `.env.example`, `.gitignore` 작성
  - `state/last_seen.json` 초기값 생성 (`{"processed_urls": []}`)
  - `output/.gitkeep` 생성

---

### Phase 2 — 핵심 모듈 (병렬 진행 가능)

- [x] **Task 2: state.py 구현** _(Task 1 완료 후)_
  - `load_state()`, `is_processed(url)`, `mark_processed(url)` 함수 구현
  - `state/last_seen.json` 읽기/쓰기

- [x] **Task 4: generator.py 구현** _(Task 1 완료 후, Task 2와 병렬)_
  - Claude API(`claude-sonnet-4-6`) 호출
  - 시스템 프롬프트 캐싱(`cache_control: ephemeral`) 적용
  - 출력: `{title, slides[], cta_text, original_url}` JSON

- [x] **Task 5: HTML 카드 템플릿 구현** _(Task 1 완료 후, Task 2·4와 병렬)_
  - `cover.html`, `content.html`, `cta.html` 작성
  - 디자인: 1080×1080px, 배경 `#191919`, 텍스트 `#FFFFFF`, 액센트 `#D4A97A`, Noto Sans KR

- [x] **Task 7: instagram.py 구현** _(Task 1 완료 후, 다른 Task와 병렬)_
  - Instagram Graph API Carousel 3단계 구현 (Container → Carousel → Publish)
  - Access Token 만료 시 GitHub Issue 자동 생성

- [x] **Task 8: slack_notifier.py 구현** _(Task 1 완료 후, 다른 Task와 병렬)_
  - Slack Incoming Webhook + Block Kit 메시지 전송
  - 커버 이미지 인라인 + 불릿 요약 + 원본 링크 형식

---

### Phase 3 — 조합 모듈

- [x] **Task 3: scraper.py 구현** _(Task 2 완료 후)_
  - `fetch_articles()`, `get_new_article()`, `get_article_content(url)` 구현
  - 신규 기사 1개만 반환 (최신순)

- [x] **Task 6: image_maker.py 구현** _(Task 4·5 완료 후)_
  - Playwright headless Chromium으로 HTML → 1080×1080px PNG
  - `output/YYYY-MM-DD-{id}/slide_NN.png` 형태로 저장

---

### Phase 4 — 통합

- [x] **Task 9: main.py 구현** _(Task 3·4·6·7·8·2 완료 후)_
  - 전체 파이프라인 오케스트레이션
  - `--dry-run` 옵션 지원 (이미지 생성까지만)
  - git push → Instagram 게시 → Slack 알림 → 상태 저장

---

### Phase 5 — 자동화

- [x] **Task 10: GitHub Actions 워크플로 구현** _(Task 9 완료 후)_
  - `card_news.yml`: 매일 00:00 UTC(09:00 KST) cron + `workflow_dispatch`
  - `cleanup.yml`: 매주 일요일, 30일 지난 `output/` 정리

---

## 병렬 진행 가능 구조

```
Task 1 (초기화)
  ├── Task 2 (state)   ──→ Task 3 (scraper) ──┐
  ├── Task 4 (gen)     ──────────────────────┐ │
  ├── Task 5 (template)──→ Task 6 (images)  ─┤ │
  ├── Task 7 (instagram)──────────────────── ┤ │
  └── Task 8 (slack)  ───────────────────────┘ │
                                               ↓
                                         Task 9 (main)
                                               ↓
                                        Task 10 (Actions)
```

---

## 기술 스택

| 역할 | 도구 |
|------|------|
| 언어 | Python 3.12 |
| AI 생성 | Anthropic SDK (`claude-sonnet-4-6`) |
| 이미지 렌더링 | Playwright (headless Chromium) |
| 크롤링 | httpx + BeautifulSoup4 |
| 템플릿 | Jinja2 |
| Instagram 게시 | Instagram Graph API v21.0 |
| Slack 알림 | Incoming Webhook + Block Kit |
| 스케줄링 | GitHub Actions cron |

---

## 환경변수 (GitHub Secrets)

| 변수명 | 설명 |
|--------|------|
| `ANTHROPIC_API_KEY` | Claude API 키 |
| `INSTAGRAM_ACCESS_TOKEN` | Instagram Graph API 토큰 (60일 유효) |
| `INSTAGRAM_USER_ID` | Instagram 비즈니스 계정 ID |
| `SLACK_WEBHOOK_URL` | Slack Incoming Webhook URL |
| `GITHUB_TOKEN` | 자동 제공 (GitHub Actions) |
| `GITHUB_USER` | GitHub 사용자명 (raw URL 생성용) |
| `GITHUB_REPO` | 레포지토리명 (raw URL 생성용) |
