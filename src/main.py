import argparse
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# src/ 기준 import
sys.path.insert(0, str(Path(__file__).parent))

from generator import generate_card_news
from image_maker import render_slides
from instagram import TokenExpiredError, post_carousel
from scraper import get_article_content, get_new_article
from slack_notifier import send_notification
from state import mark_processed


def _check_required_env() -> None:
    required = ["ANTHROPIC_API_KEY", "GITHUB_USER", "GITHUB_REPO"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        print(f"[오류] 필수 환경변수 누락: {', '.join(missing)}")
        sys.exit(1)


def _git_push(message: str, paths: list[str]) -> bool:
    try:
        subprocess.run(["git", "add"] + paths, check=True)
        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            capture_output=True,
        )
        if result.returncode == 0:
            print(f"[git] 변경사항 없음, 커밋 건너뜀")
            return True
        subprocess.run(["git", "commit", "-m", message], check=True)
        subprocess.run(["git", "push"], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[git] 오류: {e}")
        return False


def _build_raw_urls(png_paths: list[Path]) -> list[str]:
    github_user = os.environ["GITHUB_USER"]
    github_repo = os.environ["GITHUB_REPO"]
    repo_root = Path(__file__).parent.parent
    return [
        f"https://raw.githubusercontent.com/{github_user}/{github_repo}/main/{p.relative_to(repo_root)}"
        for p in png_paths
    ]


def _build_caption(card_data: dict) -> str:
    bullets = "\n".join(f"• {s['heading']}" for s in card_data["slides"][:5])
    return f"{card_data['title']}\n\n{bullets}\n\n{card_data['original_url']}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Anthropic 뉴스 카드뉴스 자동화")
    parser.add_argument("--dry-run", action="store_true", help="이미지 생성까지만 실행 (배포 없음)")
    args = parser.parse_args()

    _check_required_env()

    # 1. 새 기사 확인
    print("[1/6] 새 기사 확인 중...")
    article = get_new_article()
    if article is None:
        print("새 기사 없음. 종료합니다.")
        sys.exit(0)
    print(f"  → 발견: {article['title']} ({article['date_str']})")

    # 2. 기사 본문 수집
    print("[2/6] 기사 본문 수집 중...")
    content = get_article_content(article["url"])
    print(f"  → {len(content):,}자 수집 완료")

    # 3. 카드뉴스 내용 생성
    print("[3/6] Claude API로 한국어 카드뉴스 생성 중...")
    card_data = generate_card_news(content, article["url"])
    print(f"  → 제목: {card_data['title']}, 슬라이드: {len(card_data['slides'])}장")

    # 4. 이미지 렌더링
    print("[4/6] 카드뉴스 이미지 생성 중...")
    date_str = datetime.now().strftime("%Y-%m-%d")
    output_dir = Path(__file__).parent.parent / "output" / f"{date_str}-{article['url'].split('/')[-1][:20]}"
    png_paths = render_slides(card_data, output_dir)
    print(f"  → {len(png_paths)}장 생성 완료: {output_dir}")

    if args.dry_run:
        print("\n[dry-run] 이미지 생성 완료. 배포는 건너뜁니다.")
        for p in png_paths:
            print(f"  {p}")
        sys.exit(0)

    # 5. git push (Instagram raw URL 확보)
    print("[5/6] GitHub에 이미지 커밋 중...")
    _git_push(
        f"chore: add card news {date_str} - {card_data['title']}",
        ["output/", "state/"],
    )
    print("  → 완료. CDN 전파 대기 30초...")
    time.sleep(30)

    # 6. Instagram 게시
    instagram_posted = False
    if os.environ.get("INSTAGRAM_ACCESS_TOKEN") and os.environ.get("INSTAGRAM_USER_ID"):
        print("[6a] Instagram Carousel 게시 중...")
        try:
            image_urls = _build_raw_urls(png_paths)
            caption = _build_caption(card_data)
            post_id = post_carousel(image_urls, caption)
            instagram_posted = True
            print(f"  → 게시 완료 (post_id: {post_id})")
        except TokenExpiredError:
            print("  → Access Token 만료. GitHub Issue 생성됨.")
        except Exception as e:
            print(f"  → Instagram 게시 실패 (Slack은 계속): {e}")
    else:
        print("[6a] Instagram 환경변수 없음, 건너뜀")

    # 7. Slack 알림
    print("[6b] Slack 알림 전송 중...")
    cover_url = _build_raw_urls(png_paths)[0]
    send_notification(cover_url, card_data, len(png_paths), instagram_posted)
    print("  → 완료")

    # 8. 처리 완료 상태 저장
    mark_processed(article["url"])
    _git_push("chore: update last_seen", ["state/"])
    print(f"\n완료! 카드뉴스 {len(png_paths)}장 배포 완료.")


if __name__ == "__main__":
    main()
