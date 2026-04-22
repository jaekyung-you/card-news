# /card-news

Anthropic 뉴스 기사를 카드뉴스 이미지로 변환하는 명령어.

## 사용법

```
/card-news [URL]          # 특정 URL로 생성
/card-news                # 최신 미처리 기사 자동 탐지
/card-news --dry-run [URL] # 이미지만 생성, Slack/Instagram 전송 없음
```

## 실행 흐름

$ARGUMENTS 에서 URL과 플래그를 파싱한다.

### 1. 기사 내용 수집

URL이 주어진 경우:
```bash
python3 -c "
import sys; sys.path.insert(0, 'src')
from scraper import get_article_content
content = get_article_content('$ARGUMENTS')
print(content[:3000])
"
```

URL이 없으면 최신 미처리 기사를 자동 탐지:
```bash
python3 -c "
import sys; sys.path.insert(0, 'src')
from dotenv import load_dotenv; load_dotenv()
from scraper import get_new_article
a = get_new_article()
print(a['url'] if a else 'NONE')
"
```

### 2. 카드뉴스 JSON 생성

`src/generator.py`의 `generate_card_news(content, url)`로 Claude API 호출.
ANTHROPIC_API_KEY 환경변수가 필요하다. 없으면 사용자에게 안내.

### 3. 슬라이드 이미지 렌더링

`src/image_maker.py`의 `render_slides(card_data, output_dir)`로 PNG 생성.
출력 경로: `output/{YYYY-MM-DD}-{article-slug}/slide_NN.png`

### 4. 결과 미리보기

생성된 슬라이드 이미지를 순서대로 보여준다 (Read 도구 사용).

### 5. 배포 (--dry-run이 아닌 경우)

**GitHub 커밋** (Instagram raw URL 확보):
```bash
git add output/ state/
git commit -m "chore: add card news {date} - {title}"
git push
```

**Slack 알림** (SLACK_WEBHOOK_URL 설정 시):
```bash
python3 -c "
import sys, os; sys.path.insert(0, 'src')
from dotenv import load_dotenv; load_dotenv()
from slack_notifier import send_notification
# cover_url = raw GitHub URL of slide_01.png
# send_notification(cover_url, card_data, slide_count, instagram_posted)
"
```

**Instagram 게시** (INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_USER_ID 설정 시):
`src/instagram.py`의 `post_carousel(image_urls, caption)` 호출.

## 환경변수

| 변수 | 필수 | 설명 |
|------|------|------|
| ANTHROPIC_API_KEY | ✅ | 카드뉴스 JSON 생성 |
| SLACK_WEBHOOK_URL | 선택 | Slack 알림 |
| INSTAGRAM_ACCESS_TOKEN | 선택 | Instagram 게시 |
| INSTAGRAM_USER_ID | 선택 | Instagram 게시 |

## 디자인 가이드라인

- 배경: 베이지 `#FAF6F1`
- 주황 `#D4734A`: POINT 레이블 accent만
- 다크 `#2D2D2D`: 텍스트, 카드 배경
- 화이트 `#FFFFFF`: 비주얼 카드 배경
- 본문 텍스트 최소 26px
- 콘텐츠 수직 중앙 배치
- 템플릿 파일: `templates/cover.html`, `templates/content.html`, `templates/cta.html`
