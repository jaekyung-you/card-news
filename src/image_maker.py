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
        cover_html = cover_tpl.render(
            title=card_data["title"],
            date=datetime.now().strftime("%Y. %m. %d"),
        )
        png_paths.append(screenshot(cover_html, "slide_01.png"))

        # 내용 (slide_02 ~ slide_N-1)
        for i, slide in enumerate(slides, start=1):
            content_html = content_tpl.render(
                slide_number=i,
                total_slides=total_slides - 2,
                heading=slide["heading"],
                body=slide["body"],
            )
            png_paths.append(screenshot(content_html, f"slide_{i + 1:02d}.png"))

        # CTA (마지막)
        cta_html = cta_tpl.render(
            cta_text=card_data["cta_text"],
            original_url=card_data["original_url"],
        )
        png_paths.append(screenshot(cta_html, f"slide_{total_slides:02d}.png"))

        browser.close()

    return png_paths
