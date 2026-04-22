from datetime import datetime
from pathlib import Path
import uuid

from jinja2 import Environment, FileSystemLoader
from playwright.sync_api import sync_playwright

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
OUTPUT_DIR = Path(__file__).parent.parent / "output"


def _make_output_dir() -> Path:
    date_str = datetime.now().strftime("%Y-%m-%d")
    uid = str(uuid.uuid4())[:8]
    output_dir = OUTPUT_DIR / f"{date_str}-{uid}"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def _build_title_html(title: str, accent: str) -> str:
    if accent and accent in title:
        return title.replace(accent, f'<span class="accent">{accent}</span>', 1)
    return title


def render_slides(card_data: dict, output_dir: Path | None = None) -> list[Path]:
    if output_dir is None:
        output_dir = _make_output_dir()

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    cover_tpl = env.get_template("cover.html")
    content_tpl = env.get_template("content.html")
    cta_tpl = env.get_template("cta.html")

    slides = card_data["slides"]
    total_slides = len(slides) + 2  # 커버 + 내용 + CTA

    png_paths: list[Path] = []

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1080, "height": 1080})

        def screenshot(html: str, filename: str) -> Path:
            page.set_content(html)
            page.wait_for_load_state("networkidle")
            path = output_dir / filename
            page.screenshot(
                path=str(path),
                clip={"x": 0, "y": 0, "width": 1080, "height": 1080},
            )
            return path

        # 커버 (slide_01)
        title_html = _build_title_html(
            card_data["title"],
            card_data.get("title_accent", ""),
        )
        cover_html = cover_tpl.render(
            title_html=title_html,
            subtitle=card_data.get("subtitle", ""),
            date=datetime.now().strftime("%Y. %m. %d"),
        )
        png_paths.append(screenshot(cover_html, "slide_01.png"))

        # 내용 슬라이드 (slide_02 ~ slide_N-1)
        for i, slide in enumerate(slides, start=1):
            visual = slide.get("visual", {"type": "text", "body": slide.get("body", "")})
            visual_type = visual.get("type", "text")
            visual_items = visual.get("items", [])
            visual_bad = visual.get("bad", {})
            visual_good = visual.get("good", {})
            visual_body = visual.get("body", slide.get("body", ""))

            content_html = content_tpl.render(
                slide_number=i + 1,
                total_slides=total_slides,
                label=slide.get("label", f"POINT {i:02d}"),
                heading=slide["heading"],
                visual_type=visual_type,
                visual_items=visual_items,
                visual_bad=visual_bad,
                visual_good=visual_good,
                visual_body=visual_body,
                bottom_cta=slide.get("bottom_cta", ""),
            )
            png_paths.append(screenshot(content_html, f"slide_{i + 1:02d}.png"))

        # CTA (마지막 슬라이드)
        cta_html = cta_tpl.render(
            cta_text=card_data["cta_text"],
            original_url=card_data["original_url"],
            slide_number=total_slides,
            total_slides=total_slides,
        )
        png_paths.append(screenshot(cta_html, f"slide_{total_slides:02d}.png"))

        browser.close()

    return png_paths
