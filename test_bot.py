import datetime
import unittest
from unittest.mock import AsyncMock, patch

from bot import broadcast_test_video, format_message, pick_item, pick_video


FAKE_ITEMS = [
    {"id": "fact_1", "type": "fact", "number": 1, "text": "Rush formed in 1968."},
    {"id": "fact_2", "type": "fact", "number": 2, "text": "Neil Peart joined in 1974."},
    {"id": "video_Live_in_Rio", "type": "video", "title": "Live in Rio", "url": "https://youtu.be/abc"},
    {"id": "video_Time_Machine", "type": "video", "title": "Time Machine", "url": "https://www.youtube.com/watch?v=def"},
    {"id": "video_Non_YouTube", "type": "video", "title": "Non YouTube", "url": "https://vimeo.com/xyz"},
]

EMPTY_STATE = {"channels": [], "history": []}
FULL_STATE = {"channels": [-100111, -100222], "history": []}


def _recent_history(*item_ids):
    return [
        {"item_id": iid, "posted_at": datetime.datetime.now(datetime.timezone.utc).isoformat()}
        for iid in item_ids
    ]


class TestPickVideo(unittest.TestCase):
    def test_returns_only_youtube_videos(self):
        for _ in range(50):
            item = pick_video(FAKE_ITEMS, EMPTY_STATE)
            self.assertIn("youtube.com", item["url"] + item["url"].replace("youtu.be", "youtube.com"))
            self.assertNotEqual(item["id"], "video_Non_YouTube")

    def test_excludes_non_youtube_items(self):
        for _ in range(50):
            item = pick_video(FAKE_ITEMS, EMPTY_STATE)
            self.assertNotEqual(item["id"], "video_Non_YouTube")

    def test_url_is_youtube(self):
        for _ in range(50):
            item = pick_video(FAKE_ITEMS, EMPTY_STATE)
            self.assertTrue(
                "youtube.com" in item["url"] or "youtu.be" in item["url"],
                f"Expected a YouTube URL, got: {item['url']}",
            )

    def test_excludes_recently_posted(self):
        state = {"channels": [], "history": _recent_history("video_Live_in_Rio")}
        for _ in range(50):
            item = pick_video(FAKE_ITEMS, state)
            self.assertNotEqual(item["id"], "video_Live_in_Rio")

    def test_falls_back_when_all_youtube_videos_on_cooldown(self):
        state = {
            "channels": [],
            "history": _recent_history("video_Live_in_Rio", "video_Time_Machine"),
        }
        item = pick_video(FAKE_ITEMS, state)
        self.assertTrue(
            "youtube.com" in item["url"] or "youtu.be" in item["url"],
            "Fallback should still return a YouTube video.",
        )

    def test_raises_when_no_youtube_videos(self):
        no_youtube = [i for i in FAKE_ITEMS if i["type"] != "video" or "vimeo" in i.get("url", "")]
        with self.assertRaises(ValueError):
            pick_video(no_youtube, EMPTY_STATE)

    def test_raises_when_no_videos_at_all(self):
        facts_only = [i for i in FAKE_ITEMS if i["type"] == "fact"]
        with self.assertRaises(ValueError):
            pick_video(facts_only, EMPTY_STATE)


class TestPickItem(unittest.TestCase):
    def test_excludes_recently_posted(self):
        state = {"channels": [], "history": _recent_history("fact_1")}
        for _ in range(50):
            item = pick_item(FAKE_ITEMS, state)
            self.assertNotEqual(item["id"], "fact_1")

    def test_falls_back_when_all_on_cooldown(self):
        all_ids = [i["id"] for i in FAKE_ITEMS]
        state = {"channels": [], "history": _recent_history(*all_ids)}
        item = pick_item(FAKE_ITEMS, state)
        self.assertIn(item["id"], all_ids)


class TestFormatMessage(unittest.TestCase):
    def test_fact(self):
        msg = format_message(FAKE_ITEMS[0])
        self.assertIn("Rush Fact #1", msg)
        self.assertIn("Rush formed in 1968.", msg)

    def test_video(self):
        msg = format_message(FAKE_ITEMS[2])
        self.assertIn("https://youtu.be/abc", msg)
        self.assertIn("Live in Rio", msg)


class TestBroadcastTestVideo(unittest.IsolatedAsyncioTestCase):
    @patch("bot.load_state", return_value=EMPTY_STATE)
    async def test_no_channels_returns_zero(self, _):
        bot = AsyncMock()
        sent, failed = await broadcast_test_video(bot)
        self.assertEqual((sent, failed), (0, 0))
        bot.send_message.assert_not_called()

    @patch("bot.load_state", return_value=FULL_STATE)
    @patch("bot.load_items", return_value=FAKE_ITEMS)
    async def test_sends_to_all_channels(self, _, __):
        bot = AsyncMock()
        sent, failed = await broadcast_test_video(bot)
        self.assertEqual(sent, 2)
        self.assertEqual(failed, 0)
        self.assertEqual(len(bot.send_message.call_args_list), 2)

    @patch("bot.load_state", return_value=FULL_STATE)
    @patch("bot.load_items", return_value=FAKE_ITEMS)
    async def test_message_tagged_test_video(self, _, __):
        bot = AsyncMock()
        await broadcast_test_video(bot)
        for call in bot.send_message.call_args_list:
            self.assertIn("[test-video]", call.kwargs["text"])

    @patch("bot.load_state", return_value=FULL_STATE)
    @patch("bot.load_items", return_value=FAKE_ITEMS)
    async def test_message_contains_youtube_url(self, _, __):
        bot = AsyncMock()
        await broadcast_test_video(bot)
        text = bot.send_message.call_args_list[0].kwargs["text"]
        self.assertTrue(
            "youtube.com" in text or "youtu.be" in text,
            f"Expected a YouTube URL in message: {text}",
        )

    @patch("bot.load_state", return_value=FULL_STATE)
    @patch("bot.load_items", return_value=FAKE_ITEMS)
    async def test_message_does_not_contain_non_youtube_url(self, _, __):
        bot = AsyncMock()
        await broadcast_test_video(bot)
        for call in bot.send_message.call_args_list:
            self.assertNotIn("vimeo.com", call.kwargs["text"])

    @patch("bot.load_state", return_value=FULL_STATE)
    @patch("bot.load_items", return_value=FAKE_ITEMS)
    async def test_counts_failures(self, _, __):
        bot = AsyncMock()
        bot.send_message.side_effect = Exception("network error")
        sent, failed = await broadcast_test_video(bot)
        self.assertEqual(sent, 0)
        self.assertEqual(failed, 2)


if __name__ == "__main__":
    unittest.main()
