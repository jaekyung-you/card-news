import json
import os

import anthropic

SYSTEM_PROMPT = """당신은 한국어 SNS 카드뉴스 전문 에디터입니다.

영어 기사를 받으면 다음 JSON 형식으로 한국어 카드뉴스 데이터를 반환하세요.

필드 설명:
- title: 기사 핵심을 담은 한국어 제목 (15자 이내)
- title_accent: title 안에 포함된 강조할 핵심 단어 1개 (주황색으로 표시됨)
- subtitle: 부제목 한 줄 (40자 이내, 배경/맥락 설명)
- slides: 핵심 포인트 슬라이드 배열 (최소 3개, 최대 8개)
  - label: 슬라이드 레이블 (예: "POINT 01", "KEY INSIGHT", "FACT", "TIP 01", 영어 대문자)
  - heading: 슬라이드 소제목 (20자 이내)
  - visual: 시각화 데이터
    - type: "numbered_list" | "comparison" | "stat" | "text"
    - numbered_list → items: [{"title": "항목명", "desc": "한 줄 설명"}, ...] 3~4개
    - comparison → bad: {"label": "기존 방식", "desc": "설명"}, good: {"label": "새 방식", "desc": "설명"}
    - stat → items: [{"number": "3배", "desc": "성능 향상"}, ...] 2~4개
    - text → body: "본문 2~3문장"
  - bottom_cta: 이 슬라이드의 핵심 메시지 한 줄 (30자 이내)
- cta_text: 마지막 CTA 카드 팔로우 유도 문구 (30자 이내)

시각화 타입 선택 기준:
- 단계/기능/방법 나열 → numbered_list
- 기존 vs 새로운, 문제 vs 해결, 나쁜 예 vs 좋은 예 비교 → comparison
- 수치/통계/퍼센트 강조 → stat
- 그 외 일반 설명 → text

이모지 절대 사용 금지.

순수 JSON만 반환 (마크다운 코드블록 없이):
{
  "title": "...",
  "title_accent": "...",
  "subtitle": "...",
  "slides": [
    {
      "label": "POINT 01",
      "heading": "...",
      "visual": {"type": "numbered_list", "items": [{"title": "...", "desc": "..."}]},
      "bottom_cta": "..."
    }
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
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    data = json.loads(raw)

    if "slides" not in data or not data["slides"]:
        raise ValueError("slides 필드가 비어 있습니다")

    data["slides"] = data["slides"][:8]
    data["original_url"] = original_url
    data.setdefault("title_accent", "")
    data.setdefault("subtitle", "")

    for i, slide in enumerate(data["slides"], 1):
        slide.setdefault("label", f"POINT {i:02d}")
        slide.setdefault("bottom_cta", "")
        if "visual" not in slide:
            slide["visual"] = {"type": "text", "body": slide.get("body", "")}

    return data
