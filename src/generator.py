import json
import os

import anthropic

SYSTEM_PROMPT = """당신은 한국어 SNS 카드뉴스 전문 에디터입니다.

영어 기사를 받으면 한국어 카드뉴스용 JSON을 반환하세요.

규칙:
- title: 기사 핵심을 담은 한국어 제목 (30자 이내)
- slides: 핵심 포인트 배열, 최소 1개 최대 8개
  - heading: 슬라이드 소제목 (20자 이내)
  - body: 2문장 설명 (각 문장 30자 이내, 합계 60자 이내)
- cta_text: 팔로우 유도 문구 (30자 이내)

반드시 아래 형식의 순수 JSON만 반환하세요 (마크다운 코드블록 없이):
{
  "title": "...",
  "slides": [
    {"heading": "...", "body": "..."},
    ...
  ],
  "cta_text": "..."
}"""


def generate_card_news(article_content: str, original_url: str) -> dict:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[
            {
                "role": "user",
                "content": f"다음 기사를 한국어 카드뉴스 JSON으로 변환해주세요:\n\n{article_content}",
            }
        ],
    )

    raw = response.content[0].text.strip()
    # 코드블록 감싸인 경우 제거
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    data = json.loads(raw)

    # 필드 검증 및 보정
    if "slides" not in data or not data["slides"]:
        raise ValueError("slides 필드가 비어 있습니다")
    data["slides"] = data["slides"][:8]
    data["original_url"] = original_url

    return data
