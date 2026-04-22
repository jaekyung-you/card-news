# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Does

Anthropic 뉴스 기사를 자동으로 한국어 카드뉴스(Instagram 슬라이드)로 변환하는 파이프라인.
GitHub Actions로 매일 09:00 KST에 자동 실행되며, `/card-news` 슬래시 커맨드로 수동 실행 가능.

## Common Commands

```bash
# 의존성 설치
pip install -r requirements.txt
python -m playwright install chromium

# 이미지 생성만 (배포 없음)
python src/main.py --dry-run

# 특정 URL로 직접 테스트 렌더링
python3 -c "
import sys; sys.path.insert(0, 'src')
from image_maker import render_slides
from pathlib import Path
card_data = {...}  # 테스트 데이터
render_slides(card_data, Path('output/test'))
"

# 환경변수 로드 후 전체 파이프라인 실행
ANTHROPIC_API_KEY=... python src/main.py
```

## Pipeline Architecture

```
scraper.py          → 기사 URL 탐지 및 본문 수집 (anthropic.com/news)
generator.py        → Claude API로 한국어 카드뉴스 JSON 생성
image_maker.py      → Jinja2 + Playwright로 HTML→PNG 렌더링 (1080×1080)
instagram.py        → Instagram Graph API로 Carousel 게시
slack_notifier.py   → Slack Incoming Webhook으로 알림
state.py            → 처리된 URL 추적 (state/last_seen.json)
main.py             → 전체 파이프라인 오케스트레이션
```

## Slide Structure

각 카드뉴스는 **커버(1장) + 콘텐츠(N장) + CTA(1장)** 구조.

- `templates/cover.html` — 제목 슬라이드
- `templates/content.html` — 콘텐츠 슬라이드 (visual_type에 따라 4가지 레이아웃)
- `templates/cta.html` — 팔로우 유도 슬라이드

### `visual_type` 종류

| 타입 | 구조 | 용도 |
|------|------|------|
| `numbered_list` | 2×2 다크 카드 그리드 | 기능/단계 나열 |
| `stat` | 3열 수치 카드 | 벤치마크/통계 강조 |
| `comparison` | BEFORE/AFTER 카드 | 기존 vs 신규 비교 |
| `text` | 좌측 주황 바 + 본문 | 일반 설명 |

## Design System

| 색상 | 용도 |
|------|------|
| `#FAF6F1` | 배경 (베이지) |
| `#D4734A` | Accent only — POINT 레이블, NEW RELEASE 아이워드 |
| `#2D2D2D` | 텍스트, 다크 카드 배경 |
| `#FFFFFF` | 비주얼 카드 배경 |

- 본문 텍스트 최소 26px
- 콘텐츠 수직 중앙 배치 (`justify-content: center`)
- 슬라이드 레이블은 항상 `POINT {n}` 형식 (generator가 반환한 label은 무시)

## Generator JSON Schema

`generator.py`의 Claude API 호출이 반환하는 구조:

```json
{
  "title": "...",
  "title_accent": "강조할 단어",
  "subtitle": "부제목",
  "slides": [
    {
      "heading": "슬라이드 소제목",
      "subtitle": "보조 설명",
      "visual": { "type": "stat", "items": [...] },
      "bottom_cta": "핵심 인사이트 한 줄"
    }
  ],
  "cta_text": "CTA 문구",
  "original_url": "https://..."
}
```

## Environment Variables

| 변수 | 필수 | 설명 |
|------|------|------|
| `ANTHROPIC_API_KEY` | ✅ | 카드뉴스 JSON 생성 |
| `USER` | ✅ | GitHub 사용자명 (raw URL 생성용) |
| `REPO` | ✅ | GitHub 레포명 (raw URL 생성용) |
| `SLACK_WEBHOOK_URL` | 선택 | Slack Incoming Webhook |
| `INSTAGRAM_ACCESS_TOKEN` | 선택 | Instagram Graph API 토큰 |
| `INSTAGRAM_USER_ID` | 선택 | Instagram 계정 ID |
| `GITHUB_TOKEN` | CI | GitHub Issue 생성 (토큰 만료 알림) |

## Key Behaviors

- **중복 방지**: `state/last_seen.json`에 처리된 URL 저장. 같은 기사 재처리 안 함.
- **Instagram 토큰 만료**: 에러 코드 190 감지 시 GitHub Issue 자동 생성 후 예외 발생.
- **이미지 raw URL**: Instagram은 공개 URL 필요 → output/ 이미지를 git push 후 GitHub raw URL 사용. CDN 전파 30초 대기.
- **Slack은 Instagram 실패와 독립**: Instagram 게시 실패해도 Slack 알림은 계속 전송.
