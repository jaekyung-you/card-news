# Development Guidelines — Card News Automation

## Project Overview

- **목적**: Anthropic 뉴스(https://www.anthropic.com/news) 신규 기사 감지 → 한국어 카드뉴스 자동 생성 → Instagram(Carousel) + Slack 배포
- **실행 환경**: GitHub Actions (매일 09:00 KST = 00:00 UTC)
- **언어**: Python 3.12

---

## Project Architecture

```
card_news/
├── .github/workflows/
│   ├── card_news.yml          # 메인 cron 파이프라인
│   └── cleanup.yml            # 30일 지난 output 정리
├── src/
│   ├── main.py                # 진입점, 전체 파이프라인 오케스트레이션
│   ├── scraper.py             # Anthropic 뉴스 크롤링 + 신규 기사 감지
│   ├── generator.py           # Claude API 호출 → 카드뉴스 JSON 생성
│   ├── image_maker.py         # HTML 템플릿 → Playwright → PNG
│   ├── instagram.py           # Instagram Graph API Carousel 게시
│   ├── slack_notifier.py      # Slack Incoming Webhook 전송
│   └── state.py               # last_seen.json 읽기/쓰기
├── templates/
│   ├── cover.html             # 커버 카드 (1장)
│   ├── content.html           # 내용 카드 (n장, Jinja2 템플릿)
│   └── cta.html               # CTA 카드 (마지막 1장)
├── output/                    # 생성된 PNG (git tracked, Instagram URL용)
│   └── YYYY-MM-DD-{slug}/
│       ├── slide_01.png
│       └── ...
├── state/
│   └── last_seen.json         # 처리 완료한 기사 URL 목록
├── shrimp-rules.md
└── requirements.txt
```

---

## Code Standards

- **파일명**: snake_case
- **함수명**: snake_case, 동사로 시작 (예: `fetch_articles`, `render_slide`)
- **상수**: UPPER_SNAKE_CASE, `src/config.py`에 집중 관리
- **주석**: WHY가 명확하지 않은 경우만 작성, 설명형 주석 금지
- **타입 힌트**: 모든 함수 시그니처에 필수
- **에러 핸들링**: 외부 API 호출(Instagram, Slack, Claude, 크롤링)에만 try/except 적용

---

## Card News Specification

| 슬라이드 | 역할 | 템플릿 |
|---------|------|--------|
| 1장 (커버) | 기사 제목(한국어) + 날짜 + Anthropic 브랜딩 | `cover.html` |
| 2~9장 (내용) | 핵심 포인트 1개/장, 최대 8장 | `content.html` |
| 마지막 장 (CTA) | 팔로우 유도 + 원본 URL | `cta.html` |

- **총 슬라이드**: 최소 3장, 최대 10장 (커버 1 + 내용 1~8 + CTA 1)
- **이미지 사양**: 1080×1080px PNG
- **배경색**: `#191919`
- **텍스트색**: `#FFFFFF`
- **액센트색**: `#D4A97A`
- **폰트**: Noto Sans KR (Google Fonts CDN)
- **언어**: 모든 텍스트 한국어

---

## Claude API Rules

- **모델**: `claude-sonnet-4-6` (변경 금지)
- **시스템 프롬프트 캐싱**: `generator.py`의 시스템 프롬프트에 반드시 `cache_control` 적용
- **출력 형식**: JSON (`title`, `slides[]`, `cta_text`, `original_url`)
- `slides` 배열 길이: 1~8 (커버·CTA 제외)
- **크롤링 후 즉시 호출**: 기사 본문 전체를 컨텍스트로 전달

```python
# generator.py 시스템 프롬프트 캐싱 필수 패턴
{
    "type": "text",
    "text": SYSTEM_PROMPT,
    "cache_control": {"type": "ephemeral"}
}
```

---

## State Management Rules

- **`state/last_seen.json`** 구조: `{"processed_urls": ["https://...", ...]}`
- 새 기사 처리 후 반드시 JSON 업데이트 → git commit & push
- 한 번 실행에 **최신 1개 기사만** 처리 (여러 개면 다음 실행에 처리)
- `state/last_seen.json`은 git tracked 파일 — `.gitignore`에 추가 금지

---

## Image Hosting Rules (Instagram URL 요구사항)

- 생성된 PNG를 `output/YYYY-MM-DD-{slug}/slide_NN.png` 경로에 저장
- Instagram API 호출 **전에** git commit & push 완료 필수
- Instagram에 전달하는 URL 형식:
  ```
  https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/output/{date}-{slug}/slide_NN.png
  ```
- `GITHUB_USER`, `GITHUB_REPO`는 GitHub Actions Secret 또는 환경변수로 관리

---

## Instagram API Rules

- **3단계 Carousel 게시 순서 절대 준수**:
  1. 각 이미지 → Container 생성 (`is_carousel_item=true`)
  2. Carousel Container 생성 (`media_type=CAROUSEL`, `children` 목록)
  3. `media_publish` 호출
- 각 단계 사이 **3초 대기** (Meta API rate limit)
- Access Token 만료(60일) 시 GitHub Issue 자동 생성으로 알림
- Secrets: `INSTAGRAM_ACCESS_TOKEN`, `INSTAGRAM_USER_ID`

---

## Slack Notification Rules

- **Webhook URL**: Secret `SLACK_WEBHOOK_URL` 사용
- **메시지 구조** (Block Kit):
  1. `image_block` — 커버 PNG URL (raw GitHub)
  2. `section` — `*제목*` + 핵심 포인트 불릿
  3. `section` — 원본 링크 + "Instagram에 N장 게시됨"
- Instagram 게시 실패 시에도 Slack은 텍스트만으로 전송 (단독 실패 허용)

---

## GitHub Actions Rules

- **cron**: `'0 0 * * *'` (UTC 00:00 = KST 09:00)
- **`workflow_dispatch`** 항상 포함 (수동 실행용)
- **필수 Secrets**:
  - `ANTHROPIC_API_KEY`
  - `INSTAGRAM_ACCESS_TOKEN`
  - `INSTAGRAM_USER_ID`
  - `SLACK_WEBHOOK_URL`
  - `GITHUB_TOKEN` (자동 제공)
- `output/`과 `state/last_seen.json` 변경 후 반드시 `git push`
- Playwright 설치: `playwright install chromium --with-deps`

---

## Key File Interaction Standards

| 변경 대상 | 동시에 확인/수정해야 할 파일 |
|----------|--------------------------|
| `templates/*.html` | `image_maker.py` (뷰포트 크기, 선택자 확인) |
| `generator.py` (JSON 스키마 변경) | `image_maker.py`, `slack_notifier.py` (필드 참조 확인) |
| `state.py` | `main.py` (호출 위치 확인) |
| `requirements.txt` | `.github/workflows/card_news.yml` (pip install 단계) |
| `card_news.yml` (Secrets 추가) | README.md의 환경변수 설정 섹션 |

---

## Workflow Data Flow

```
GitHub Actions cron trigger
  → scraper.py: fetch_articles() → compare with last_seen.json
  → (새 기사 없으면 early exit)
  → generator.py: generate_card_news(article) → JSON
  → image_maker.py: render_slides(json) → PNG files in output/
  → git commit & push (output/ + state/)
  → instagram.py: post_carousel(png_urls) → Carousel 게시
  → slack_notifier.py: send_notification(cover_url, summary) → Webhook 전송
  → state.py: update_last_seen(article_url)
```

---

## AI Decision Standards

| 상황 | 결정 기준 |
|------|---------|
| 슬라이드 수 결정 | 기사 본문 섹션 수 기준, 8장 초과 시 중요도 순으로 잘라냄 |
| API 오류 발생 | Instagram 실패 → Slack은 계속 전송. Slack 실패 → 로그만 남기고 종료 |
| 중복 기사 감지 | `last_seen.json`의 URL 목록과 정확히 일치하면 skip |
| 새 기사 여러 개 | 가장 최신 1개만 처리, 나머지는 다음 실행에서 처리 |
| Access Token 만료 | GitHub Issue 생성 후 해당 실행 중단 |

---

## Prohibited Actions

- `output/` 폴더를 `.gitignore`에 추가 금지 (Instagram URL로 사용)
- `state/last_seen.json`을 `.gitignore`에 추가 금지
- Claude 모델을 `claude-sonnet-4-6` 외 다른 모델로 변경 금지
- Instagram API 3단계 순서 변경 또는 단계 생략 금지
- 개인 Instagram 계정 사용 금지 (비즈니스/크리에이터 계정 필수)
- 시스템 프롬프트 캐싱 제거 금지
- 한 실행에 2개 이상의 기사 처리 금지
- 이미지 크기 1080×1080px 변경 금지
- 카드뉴스 내용을 영어로 작성 금지 (한국어 전용)
