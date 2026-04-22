import os

import httpx


def send_notification(
    cover_url: str,
    card_data: dict,
    slide_count: int,
    instagram_posted: bool,
) -> None:
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL", "")
    if not webhook_url:
        print("[Slack] SLACK_WEBHOOK_URL 미설정, 전송 건너뜀")
        return

    title = card_data.get("title", "")
    slides = card_data.get("slides", [])
    original_url = card_data.get("original_url", "")

    bullet_lines = "\n".join(f"• {s['heading']}" for s in slides[:5])
    summary_text = f"*{title}*\n{bullet_lines}"

    blocks = [
        {
            "type": "image",
            "image_url": cover_url,
            "alt_text": title,
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": summary_text},
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"📎 원본 보기: {original_url}"},
        },
    ]

    if instagram_posted:
        blocks.append(
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"📸 Instagram에 카드뉴스 {slide_count}장 게시됨",
                    }
                ],
            }
        )

    try:
        resp = httpx.post(webhook_url, json={"blocks": blocks}, timeout=10)
        if resp.status_code != 200:
            print(f"[Slack] 전송 실패: {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"[Slack] 전송 오류: {e}")
