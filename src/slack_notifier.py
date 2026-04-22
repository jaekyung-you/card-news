import os

import httpx


def _extract_bullets(visual: dict, bottom_cta: str) -> list[str]:
    vtype = visual.get("type", "text")
    bullets = []

    if vtype == "numbered_list":
        for item in visual.get("items", []):
            title = item.get("title", "")
            desc = item.get("desc", "").replace("\n", " ")
            bullets.append(f"• *{title}* — {desc}" if desc else f"• {title}")

    elif vtype == "stat":
        for item in visual.get("items", []):
            number = item.get("number", "")
            desc = item.get("desc", "").replace("\n", " ")
            bullets.append(f"• *{number}* {desc}")

    elif vtype == "comparison":
        bad = visual.get("bad", {})
        good = visual.get("good", {})
        if bad:
            label = bad.get("label", "")
            desc = bad.get("desc", "").replace("\n", " ")
            bullets.append(f"• 이전: *{label}* — {desc}" if desc else f"• 이전: {label}")
        if good:
            label = good.get("label", "")
            desc = good.get("desc", "").replace("\n", " ")
            bullets.append(f"• 이후: *{label}* — {desc}" if desc else f"• 이후: {label}")

    elif vtype == "text":
        body = visual.get("body", "")
        if body:
            bullets.append(f"• {body}")

    if bottom_cta:
        bullets.append(f"• {bottom_cta}")

    return bullets


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
    subtitle = card_data.get("subtitle", "")
    slides = card_data.get("slides", [])
    original_url = card_data.get("original_url", "")

    lines = [f"*{title}*"]
    if subtitle:
        lines.append(f"_{subtitle}_")
    lines.append("")

    for i, slide in enumerate(slides[:6], 1):
        heading = slide.get("heading", "")
        bottom_cta = slide.get("bottom_cta", "")
        visual = slide.get("visual", {})

        lines.append(f"*{i}. {heading}*")
        lines.extend(_extract_bullets(visual, bottom_cta))
        lines.append("")

    if instagram_posted:
        lines.append(f"📸 Instagram에 카드뉴스 {slide_count}장 게시됨")
        lines.append("")

    lines.append(f"🔗 원본 보기: {original_url}")

    blocks = [
        {
            "type": "image",
            "image_url": cover_url,
            "alt_text": title,
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": "\n".join(lines)},
        },
    ]

    try:
        resp = httpx.post(
            webhook_url,
            json={"blocks": blocks, "unfurl_links": True},
            timeout=10,
        )
        if resp.status_code != 200:
            print(f"[Slack] 전송 실패: {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"[Slack] 전송 오류: {e}")
