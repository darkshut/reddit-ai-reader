"""個人、非商業、唯讀的 Reddit AI 討論閱讀器雛形。"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable

TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
API_BASE_URL = "https://oauth.reddit.com"
ALLOWED_SUBREDDITS = (
    "LocalLLaMA",
    "MachineLearning",
    "artificial",
    "OpenAI",
    "ClaudeAI",
    "ChatGPT",
)
DEFAULT_SUBREDDITS = ALLOWED_SUBREDDITS[:3]
MAX_SUBREDDITS_PER_RUN = 6
DEFAULT_LIMIT = 5
MAX_LIMIT = 25
SUBREDDIT_PATTERN = re.compile(r"^[A-Za-z0-9_]+$")
APP_ID = "personal-reddit-ai-reader"
APP_VERSION = "0.1.0"


@dataclass(frozen=True)
class Config:
    client_id: str
    client_secret: str
    reddit_username: str

    @classmethod
    def from_environment(cls) -> "Config":
        values = {
            "client_id": os.environ.get("REDDIT_CLIENT_ID", "").strip(),
            "client_secret": os.environ.get("REDDIT_CLIENT_SECRET", "").strip(),
            "reddit_username": os.environ.get("REDDIT_USERNAME", "").strip(),
        }
        environment_names = {
            "client_id": "REDDIT_CLIENT_ID",
            "client_secret": "REDDIT_CLIENT_SECRET",
            "reddit_username": "REDDIT_USERNAME",
        }
        missing = [environment_names[name] for name, value in values.items() if not value]
        if missing:
            raise ValueError(f"缺少必要環境變數：{', '.join(missing)}")
        return cls(**values)

    @property
    def user_agent(self) -> str:
        return f"script:{APP_ID}:v{APP_VERSION} (by /u/{self.reddit_username})"


OpenUrl = Callable[..., Any]


class RedditReader:
    def __init__(self, config: Config, open_url: OpenUrl = urllib.request.urlopen):
        self.config = config
        self.open_url = open_url

    def fetch_access_token(self) -> str:
        credentials = f"{self.config.client_id}:{self.config.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("ascii")
        body = urllib.parse.urlencode({"grant_type": "client_credentials"}).encode("ascii")
        request = urllib.request.Request(
            TOKEN_URL,
            data=body,
            headers={
                "Authorization": f"Basic {encoded_credentials}",
                "User-Agent": self.config.user_agent,
            },
            method="POST",
        )
        response = self._read_json(request)
        access_token = response.get("access_token")
        if not isinstance(access_token, str) or not access_token:
            raise RuntimeError("Reddit OAuth 回應沒有 access_token")
        return access_token

    def fetch_new_posts(self, subreddit: str, limit: int, access_token: str) -> list[dict[str, Any]]:
        validate_subreddit(subreddit)
        if not 1 <= limit <= MAX_LIMIT:
            raise ValueError(f"limit 必須介於 1 與 {MAX_LIMIT}")

        query = urllib.parse.urlencode({"limit": limit, "raw_json": 1})
        url = f"{API_BASE_URL}/r/{subreddit}/new?{query}"
        request = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {access_token}",
                "User-Agent": self.config.user_agent,
            },
        )
        response = self._read_json(request)
        children = response.get("data", {}).get("children", [])
        return [child["data"] for child in children if isinstance(child, dict) and "data" in child]

    def _read_json(self, request: urllib.request.Request) -> dict[str, Any]:
        with self.open_url(request, timeout=20) as response:
            payload = json.load(response)
        if not isinstance(payload, dict):
            raise RuntimeError("Reddit API 回應格式不正確")
        return payload


def validate_subreddit(subreddit: str) -> None:
    if not SUBREDDIT_PATTERN.fullmatch(subreddit):
        raise ValueError(f"無效的 subreddit 名稱：{subreddit}")
    if subreddit not in ALLOWED_SUBREDDITS:
        raise ValueError(f"不在核准清單中的 subreddit：{subreddit}")


def validate_subreddit_count(subreddits: list[str]) -> None:
    if len(subreddits) > MAX_SUBREDDITS_PER_RUN:
        raise ValueError(f"每次最多讀取 {MAX_SUBREDDITS_PER_RUN} 個 subreddit")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="唯讀擷取少量 AI subreddit 新文章")
    parser.add_argument("--subreddit", action="append", dest="subreddits")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    subreddits = args.subreddits or list(DEFAULT_SUBREDDITS)
    validate_subreddit_count(subreddits)
    config = Config.from_environment()
    reader = RedditReader(config)
    access_token = reader.fetch_access_token()

    for subreddit in subreddits:
        posts = reader.fetch_new_posts(subreddit, args.limit, access_token)
        print(f"\n## r/{subreddit}")
        for post in posts:
            title = post.get("title", "(無標題)")
            permalink = post.get("permalink", "")
            print(f"- {title}: https://www.reddit.com{permalink}")


if __name__ == "__main__":
    main()
