import io
import os
import unittest
from unittest.mock import patch

from reddit_ai_reader import Config, RedditReader, validate_subreddit, validate_subreddit_count


class JsonResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


class RedditReaderTests(unittest.TestCase):
    def test_config_requires_all_environment_variables(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(
                ValueError,
                "REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME",
            ):
                Config.from_environment()

    def test_validate_subreddit_rejects_a_url(self):
        with self.assertRaisesRegex(ValueError, "無效"):
            validate_subreddit("https://reddit.com/r/LocalLLaMA")

    def test_validate_subreddit_rejects_a_non_ai_community(self):
        with self.assertRaisesRegex(ValueError, "核准清單"):
            validate_subreddit("unrelated")

    def test_validate_subreddit_count_rejects_more_than_six(self):
        with self.assertRaisesRegex(ValueError, "最多讀取 6 個"):
            validate_subreddit_count(["LocalLLaMA"] * 7)

    def test_fetch_new_posts_uses_read_only_oauth_request(self):
        requests = []

        def open_url(request, timeout):
            requests.append((request, timeout))
            return JsonResponse(b'{"data":{"children":[{"data":{"title":"News","permalink":"/r/test/1"}}]}}')

        config = Config("client-id", "client-secret", "darkshutor")
        reader = RedditReader(config, open_url=open_url)
        posts = reader.fetch_new_posts("LocalLLaMA", 3, "access-token")

        self.assertEqual(posts[0]["title"], "News")
        self.assertIn("/r/LocalLLaMA/new?", requests[0][0].full_url)
        self.assertEqual(requests[0][0].get_header("Authorization"), "Bearer access-token")
        self.assertIn("/u/darkshutor", requests[0][0].get_header("User-agent"))
        self.assertEqual(requests[0][1], 20)


if __name__ == "__main__":
    unittest.main()
