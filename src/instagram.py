import os
import time

import httpx

GRAPH_API_BASE = "https://graph.instagram.com/v21.0"


class TokenExpiredError(Exception):
    pass


def _check_token_error(response: dict) -> None:
    error = response.get("error", {})
    if error.get("code") == 190:
        _create_github_issue()
        raise TokenExpiredError("Instagram Access Token이 만료되었습니다. GitHub Issue를 생성했습니다.")


def _create_github_issue() -> None:
    github_token = os.environ.get("GITHUB_TOKEN", "")
    github_user = os.environ.get("GITHUB_USER", "")
    github_repo = os.environ.get("GITHUB_REPO", "")
    if not all([github_token, github_user, github_repo]):
        return
    httpx.post(
        f"https://api.github.com/repos/{github_user}/{github_repo}/issues",
        headers={
            "Authorization": f"Bearer {github_token}",
            "Accept": "application/vnd.github+json",
        },
        json={
            "title": "Instagram Access Token 만료 갱신 필요",
            "body": "Instagram Access Token이 만료되었습니다.\n\nMeta Developer Console에서 새 토큰을 발급하고 GitHub Secret `INSTAGRAM_ACCESS_TOKEN`을 업데이트하세요.",
        },
        timeout=10,
    )


def _get_access_token() -> str:
    return os.environ["INSTAGRAM_ACCESS_TOKEN"]


def _get_user_id() -> str:
    return os.environ["INSTAGRAM_USER_ID"]


def post_carousel(image_urls: list[str], caption: str) -> str:
    access_token = _get_access_token()
    user_id = _get_user_id()

    # Step 1: 각 이미지 Container 생성
    container_ids = []
    for url in image_urls:
        resp = httpx.post(
            f"{GRAPH_API_BASE}/{user_id}/media",
            params={
                "image_url": url,
                "is_carousel_item": "true",
                "access_token": access_token,
            },
            timeout=30,
        )
        data = resp.json()
        _check_token_error(data)
        if "id" not in data:
            raise RuntimeError(f"Container 생성 실패: {data}")
        container_ids.append(data["id"])
        time.sleep(3)

    # Step 2: Carousel Container 생성
    resp = httpx.post(
        f"{GRAPH_API_BASE}/{user_id}/media",
        params={
            "media_type": "CAROUSEL",
            "children": ",".join(container_ids),
            "caption": caption,
            "access_token": access_token,
        },
        timeout=30,
    )
    data = resp.json()
    _check_token_error(data)
    if "id" not in data:
        raise RuntimeError(f"Carousel Container 생성 실패: {data}")
    carousel_id = data["id"]
    time.sleep(3)

    # Step 3: 게시
    resp = httpx.post(
        f"{GRAPH_API_BASE}/{user_id}/media_publish",
        params={
            "creation_id": carousel_id,
            "access_token": access_token,
        },
        timeout=30,
    )
    data = resp.json()
    _check_token_error(data)
    if "id" not in data:
        raise RuntimeError(f"게시 실패: {data}")

    return data["id"]
