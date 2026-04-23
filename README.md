# card-news

Anthropic 공식 뉴스를 자동으로 한국어 카드뉴스(Instagram 슬라이드)로 변환하고 Slack으로 요약 전송하는 자동화 파이프라인.

GitHub Actions로 매일 09:00 KST에 자동 실행되며, `/card-news` Claude Code 슬래시 커맨드로 수동 실행 가능.

---

## 파이프라인 흐름

```
anthropic.com/news 크롤링
        ↓
미처리 기사 탐지 (state/last_seen.json)
        ↓
Claude API → 한국어 카드뉴스 JSON 생성
        ↓
Playwright → HTML 템플릿 → PNG 슬라이드 렌더링
        ↓
GitHub 커밋 (raw URL 확보)
        ↓
Instagram Carousel 게시 + Slack 알림 전송
```

---

## 슬라이드 구조

각 카드뉴스는 **커버 1장 + 콘텐츠 N장 + CTA 1장** 구조 (총 최대 10장).

| 슬라이드 | 템플릿 | 역할 |
|---------|--------|------|
| slide_01 | `cover.html` | 제목 + 부제목 |
| slide_02 ~ N-1 | `content.html` | 핵심 포인트 (visual_type별 레이아웃) |
| slide_N | `cta.html` | 팔로우 유도 + 원본 링크 |

### visual_type 종류

| 타입 | 레이아웃 | 사용 케이스 |
|------|---------|-----------|
| `numbered_list` | 2×2 다크 카드 그리드 | 기능/단계 나열 |
| `stat` | 3열 수치 카드 | 벤치마크·통계 강조 |
| `comparison` | BEFORE / AFTER 카드 | 기존 vs 신규 비교 |
| `text` | 좌측 주황 바 + 본문 | 일반 설명 |

---

## 디자인 시스템

Anthropic 공식 문서 색감 기반.

| 색상 | 코드 | 용도 |
|------|------|------|
| 베이지 | `#FAF6F1` | 슬라이드 배경 |
| 주황 | `#D4734A` | Accent only — POINT 레이블, 아이워드 |
| 다크 | `#2D2D2D` | 텍스트, 내부 카드 배경 |
| 화이트 | `#FFFFFF` | 비주얼 카드 배경 |

- 본문 텍스트 최소 **26px**
- 콘텐츠 수직 중앙 배치
- 슬라이드 레이블 항상 `POINT N` 형식 (generator 반환값 무시)

---

## Slack 알림 포맷

이미지 없이 계층형 텍스트 요약 전송. URL unfurl로 기사 썸네일 자동 표시.

```
*Claude Opus 4.7*
_코딩·비전·설계 전 영역에서 이전 세대를 압도_

*1. 성능 수치가 말한다*
• *+13%* 코딩 벤치마크 해결률 향상
• *-21%* 문서 추론 오류 감소
• *3×* 생산 태스크 해결 수
• 이전에 감독이 필요했던 복잡한 작업을 이제 완전히 위임할 수 있는 수준에 도달했다.

...

🔗 원본 보기: https://www.anthropic.com/news/...
```

- 소제목 최소 4개, 섹션당 bullet 최소 3개
- `bottom_cta`(핵심 인사이트)를 각 섹션 마지막 bullet로 항상 포함
- URL은 raw URL로만 작성 (썸네일 unfurl)

<img width="600" alt="스크린샷 2026-04-23 오후 12 39 44" src="https://github.com/user-attachments/assets/d16b48d2-2cb3-4148-bca9-f8da1e052924" />


---

## 로컬 실행

```bash
# 의존성 설치
pip install -r requirements.txt
python -m playwright install chromium

# .env 파일 설정
cp .env.example .env  # 아래 환경변수 항목 참고

# 이미지 생성만 (배포 없음)
python src/main.py --dry-run

# 전체 파이프라인 실행
python src/main.py
```

---

## 환경변수

| 변수 | 필수 | 설명 |
|------|------|------|
| `ANTHROPIC_API_KEY` | ✅ | 카드뉴스 JSON 생성 (Claude API) |
| `USER` | ✅ | GitHub 사용자명 (raw URL 생성용) |
| `REPO` | ✅ | GitHub 레포명 (raw URL 생성용) |
| `SLACK_WEBHOOK_URL` | 선택 | Slack Incoming Webhook URL |
| `INSTAGRAM_ACCESS_TOKEN` | 선택 | Instagram Graph API 토큰 |
| `INSTAGRAM_USER_ID` | 선택 | Instagram 계정 ID |
| `GITHUB_TOKEN` | CI | Instagram 토큰 만료 시 Issue 자동 생성 |

---

## GitHub Actions

`.github/workflows/card_news.yml`에 정의.

- **자동 실행**: 매일 09:00 KST (`cron: '0 0 * * *'`)
- **수동 실행**: GitHub Actions 탭 → `workflow_dispatch`

GitHub Secrets에 등록 필요한 항목: `ANTHROPIC_API_KEY`, `SLACK_WEBHOOK_URL`, `INSTAGRAM_ACCESS_TOKEN`, `INSTAGRAM_USER_ID`  
GitHub Variables: `USER`, `REPO`

---

## Claude Code 슬래시 커맨드

| 커맨드 | 설명 |
|--------|------|
| `/card-news [URL]` | 특정 URL 또는 최신 미처리 기사로 카드뉴스 생성 |
| `/card-news --dry-run [URL]` | 이미지 생성만, Slack/Instagram 전송 없음 |
| `/slack-notify` | Slack 메시지 포맷 가이드라인 참고 |

---

## 프로젝트 구조

```
card-news/
├── src/
│   ├── main.py           # 파이프라인 오케스트레이션
│   ├── scraper.py        # 기사 크롤링 (anthropic.com/news)
│   ├── generator.py      # Claude API → 카드뉴스 JSON
│   ├── image_maker.py    # Jinja2 + Playwright → PNG
│   ├── slack_notifier.py # Slack 알림 전송
│   ├── instagram.py      # Instagram Graph API
│   └── state.py          # 처리된 URL 추적
├── templates/
│   ├── cover.html        # 커버 슬라이드
│   ├── content.html      # 콘텐츠 슬라이드
│   └── cta.html          # CTA 슬라이드
├── output/               # 생성된 PNG (git 추적)
├── state/
│   └── last_seen.json    # 처리 완료 URL 목록
├── .claude/
│   └── commands/
│       ├── card-news.md  # /card-news 슬래시 커맨드
│       └── slack-notify.md # /slack-notify 슬래시 커맨드
├── CLAUDE.md             # Claude Code 프로젝트 가이드
└── .github/workflows/
    └── card_news.yml     # GitHub Actions 자동화
```
