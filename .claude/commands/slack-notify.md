# /slack-notify

카드뉴스 생성 결과를 Slack에 전송하는 명령어.
`src/slack_notifier.py`의 `send_notification()`을 직접 호출하거나, 메시지 포맷을 수정할 때 이 가이드를 참고한다.

## 메시지 포맷 규칙

### 구조
```
*{제목}*
_{부제목}_

*1. {슬라이드 헤딩}*
• bullet 1
• bullet 2
• bullet 3
• (핵심 인사이트 bottom_cta)

*2. ...*
...

🔗 원본 보기: {URL}   ← 반드시 raw URL (썸네일 자동 표시)
```

### 필수 조건
- 소제목(섹션)은 **최소 4개** (`slides[:6]` 범위 내)
- 섹션당 bullet point **최소 3개** — visual 데이터 + bottom_cta로 채움
- visual_type별 bullet 추출 방식:
  - `stat` → `• *{number}* {desc}` (수치 강조)
  - `numbered_list` → `• *{title}* — {desc}`
  - `comparison` → `• 이전: *{bad.label}*`, `• 이후: *{good.label}*`
  - `text` → `• {body}`
- `bottom_cta`는 해당 섹션의 마지막 bullet로 **항상** 추가
- URL은 `<URL|텍스트>` 하이퍼링크 형식 **금지** → raw URL만 사용 (Slack 썸네일 unfurl용)
- `unfurl_links: True`를 payload에 포함

## 테스트 실행

```bash
python3 -c "
import sys; sys.path.insert(0, 'src')
from dotenv import load_dotenv; load_dotenv()
from slack_notifier import send_notification
# card_data에 visual 데이터 포함 필수
send_notification('', card_data, slide_count, False)
"
```

## 환경변수
- `SLACK_WEBHOOK_URL`: Incoming Webhook URL (`.env` 또는 GitHub Secret)
