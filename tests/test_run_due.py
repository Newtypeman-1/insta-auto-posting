import json

import pytest
from datetime import datetime, timezone

from autopost.errors import AuthError, PublishError
from autopost.scheduler import run_due


class FakePublisher:
    """실제 인스타그램 대신 게시 요청을 기록하는 가짜 게시기."""

    def __init__(self):
        self.published = []

    def publish(self, image_url, caption):
        self.published.append((image_url, caption))
        return f"media-{len(self.published)}"


def write_queue(path, posts):
    path.write_text(json.dumps(posts, ensure_ascii=False), encoding="utf-8")


def read_queue(path):
    return json.loads(path.read_text(encoding="utf-8"))


NOW = datetime(2026, 11, 4, 12, 0, tzinfo=timezone.utc)


def test_due_post_is_published_and_marked_posted(tmp_path):
    queue = tmp_path / "queue.json"
    write_queue(queue, [
        {
            "id": "first",
            "image_url": "https://example.com/cat.jpg",
            "caption": "첫 자동 포스팅",
            "scheduled_at": "2026-11-04T11:00:00+00:00",
        }
    ])
    publisher = FakePublisher()

    run_due(queue, publisher, NOW)

    assert publisher.published == [("https://example.com/cat.jpg", "첫 자동 포스팅")]
    saved = read_queue(queue)[0]
    assert saved["status"] == "posted"
    assert saved["media_id"] == "media-1"


def test_running_twice_does_not_post_the_same_item_again(tmp_path):
    queue = tmp_path / "queue.json"
    write_queue(queue, [
        {
            "id": "first",
            "image_url": "https://example.com/cat.jpg",
            "caption": "첫 자동 포스팅",
            "scheduled_at": "2026-11-04T11:00:00+00:00",
        }
    ])
    publisher = FakePublisher()

    run_due(queue, publisher, NOW)
    run_due(queue, publisher, NOW)

    assert len(publisher.published) == 1
    assert read_queue(queue)[0]["media_id"] == "media-1"


class RejectingPublisher(FakePublisher):
    """특정 이미지 URL은 인스타그램이 거절하는 가짜 게시기."""

    def __init__(self, rejected_url, message):
        super().__init__()
        self.rejected_url = rejected_url
        self.message = message

    def publish(self, image_url, caption):
        if image_url == self.rejected_url:
            raise PublishError(self.message)
        return super().publish(image_url, caption)


def test_failed_post_is_recorded_and_the_rest_still_go_out(tmp_path):
    queue = tmp_path / "queue.json"
    write_queue(queue, [
        {"id": "broken", "image_url": "https://example.com/missing.jpg",
         "caption": "이미지가 없는 글", "scheduled_at": "2026-11-04T10:00:00+00:00"},
        {"id": "ok", "image_url": "https://example.com/cat.jpg",
         "caption": "정상 글", "scheduled_at": "2026-11-04T11:00:00+00:00"},
    ])
    publisher = RejectingPublisher("https://example.com/missing.jpg", "Media download has failed")

    run_due(queue, publisher, NOW)

    broken, ok = read_queue(queue)
    assert broken["status"] == "failed"
    assert broken["error"] == "Media download has failed"
    assert ok["status"] == "posted"


def test_failed_post_is_not_retried_on_the_next_run(tmp_path):
    queue = tmp_path / "queue.json"
    write_queue(queue, [
        {"id": "broken", "image_url": "https://example.com/missing.jpg",
         "caption": "이미지가 없는 글", "scheduled_at": "2026-11-04T10:00:00+00:00"},
    ])
    publisher = RejectingPublisher("https://example.com/missing.jpg", "Media download has failed")
    run_due(queue, publisher, NOW)

    publisher.rejected_url = None
    run_due(queue, publisher, NOW)

    assert publisher.published == []
    assert read_queue(queue)[0]["status"] == "failed"


def test_post_scheduled_for_later_is_left_waiting(tmp_path):
    queue = tmp_path / "queue.json"
    write_queue(queue, [
        {"id": "later", "image_url": "https://example.com/cat.jpg",
         "caption": "내일 올릴 글", "scheduled_at": "2026-11-05T09:00:00+00:00"},
    ])
    publisher = FakePublisher()

    run_due(queue, publisher, NOW)

    assert publisher.published == []
    assert "status" not in read_queue(queue)[0]


def test_invalid_post_is_marked_failed_without_calling_instagram(tmp_path):
    queue = tmp_path / "queue.json"
    write_queue(queue, [
        {"id": "no-tz", "image_url": "https://example.com/cat.jpg",
         "caption": "시간대 없는 글", "scheduled_at": "2026-11-04T11:00"},
        {"id": "ok", "image_url": "https://example.com/dog.jpg",
         "caption": "정상 글", "scheduled_at": "2026-11-04T11:00:00+00:00"},
    ])
    publisher = FakePublisher()

    run_due(queue, publisher, NOW)

    no_tz, ok = read_queue(queue)
    assert no_tz["status"] == "failed"
    assert no_tz["error"] == "예약 시각에 시간대가 없음 (예: 2026-11-04T20:00:00+09:00)"
    assert publisher.published == [("https://example.com/dog.jpg", "정상 글")]


class ExpiredTokenPublisher(FakePublisher):
    """토큰이 만료돼서 모든 요청이 거절되는 가짜 게시기."""

    def publish(self, image_url, caption):
        raise AuthError("Error validating access token: Session has expired (code 190)")


def test_expired_token_leaves_posts_waiting_and_stops(tmp_path):
    queue = tmp_path / "queue.json"
    write_queue(queue, [
        {"id": "first", "image_url": "https://example.com/cat.jpg",
         "caption": "첫 글", "scheduled_at": "2026-11-04T10:00:00+00:00"},
    ])

    with pytest.raises(AuthError):
        run_due(queue, ExpiredTokenPublisher(), NOW)

    assert "status" not in read_queue(queue)[0]
