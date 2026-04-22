from datetime import datetime

import httpx
from bs4 import BeautifulSoup

from state import is_processed

BASE_URL = "https://www.anthropic.com"
NEWS_URL = f"{BASE_URL}/news"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CardNewsBot/1.0)"}


def fetch_articles() -> list[dict]:
    r = httpx.get(NEWS_URL, follow_redirects=True, timeout=15, headers=HEADERS)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    articles = []
    seen_urls = set()

    for link in soup.find_all("a", href=True):
        href = link["href"]
        if "/news/" not in href or href == "/news/":
            continue
        url = BASE_URL + href if href.startswith("/") else href
        if url in seen_urls:
            continue
        seen_urls.add(url)

        # 제목: h2/h3 우선, 없으면 class명에 'title' 포함하는 span
        title_el = link.find(["h2", "h3"])
        if not title_el:
            title_el = next(
                (s for s in link.find_all("span") if any("title" in c for c in s.get("class", []))),
                None,
            )
        title = title_el.get_text(strip=True) if title_el else ""

        # 날짜: time 태그
        time_el = link.find("time")
        date_str = time_el.get_text(strip=True) if time_el else ""

        # 요약: p 태그
        p_el = link.find("p")
        summary = p_el.get_text(strip=True) if p_el else ""

        if not title or not date_str:
            continue

        try:
            date = datetime.strptime(date_str, "%b %d, %Y")
        except ValueError:
            continue

        articles.append({
            "title": title,
            "url": url,
            "date": date,
            "date_str": date_str,
            "summary": summary,
        })

    articles.sort(key=lambda a: a["date"], reverse=True)
    return articles


def get_new_article() -> dict | None:
    articles = fetch_articles()
    for article in articles:
        if not is_processed(article["url"]):
            return article
    return None


def get_article_content(url: str) -> str:
    r = httpx.get(url, follow_redirects=True, timeout=15, headers=HEADERS)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    article_el = soup.find("article") or soup.find("main")
    if not article_el:
        return r.get_text(separator="\n", strip=True)
    return article_el.get_text(separator="\n", strip=True)
