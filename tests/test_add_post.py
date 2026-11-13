import json

import pytest

from autopost.adding import AddError, add_post

JPEG_START = b"\xff\xd8\xff\xe0\x00\x10JFIF"
PNG_START = b"\x89PNG\r\n\x1a\n"


def fake_fetch(content):
    """URL의 앞부분을 돌려주는 가짜. 진짜는 네트워크로 받아 온다."""
    def fetch(url):
        return content
    return fetch


def write_queue(path, posts):
    path.write_text(json.dumps(posts, ensure_ascii=False), encoding="utf-8")


def read_queue(path):
    return json.loads(path.read_text(encoding="utf-8"))


FIRST = {
    "id": "first-post",
    "image_url": "https://example.com/first.jpg",
    "caption": "첫 글",
    "scheduled_at": "2026-11-12T00:00:00+09:00",
    "status": "posted",
}


def test_jpeg_url_is_added_to_the_queue_as_a_waiting_post(tmp_path):
    queue = tmp_path / "queue.json"
    write_queue(queue, [FIRST])

    add_post(queue, "https://example.com/second.jpg", "두 번째 글 #autopost",
             "2026-11-14T20:00:00+09:00", fetch=fake_fetch(JPEG_START))

    posts = read_queue(queue)
    assert posts[0] == FIRST
    assert posts[1] == {
        "id": "post-2",
        "image_url": "https://example.com/second.jpg",
        "caption": "두 번째 글 #autopost",
        "scheduled_at": "2026-11-14T20:00:00+09:00",
    }


def test_png_is_refused_and_the_queue_is_left_alone(tmp_path):
    queue = tmp_path / "queue.json"
    write_queue(queue, [FIRST])

    with pytest.raises(AddError, match="JPEG가 아님"):
        add_post(queue, "https://example.com/photo.jpg", "확장자만 jpg인 PNG",
                 "2026-11-14T20:00:00+09:00", fetch=fake_fetch(PNG_START))

    assert read_queue(queue) == [FIRST]


def test_schedule_without_timezone_is_refused_before_it_reaches_the_queue(tmp_path):
    queue = tmp_path / "queue.json"
    write_queue(queue, [FIRST])

    with pytest.raises(AddError, match="시간대가 없음"):
        add_post(queue, "https://example.com/second.jpg", "두 번째 글",
                 "2026-11-14T20:00", fetch=fake_fetch(JPEG_START))

    assert read_queue(queue) == [FIRST]


def test_caption_over_2200_characters_is_refused(tmp_path):
    queue = tmp_path / "queue.json"
    write_queue(queue, [FIRST])

    with pytest.raises(AddError, match="2200자를 넘음"):
        add_post(queue, "https://example.com/second.jpg", "가" * 2201,
                 "2026-11-14T20:00:00+09:00", fetch=fake_fetch(JPEG_START))

    assert read_queue(queue) == [FIRST]


def unreachable(url):
    raise OSError("HTTP Error 404: Not Found")


def test_url_that_cannot_be_opened_is_refused_with_a_hint(tmp_path):
    queue = tmp_path / "queue.json"
    write_queue(queue, [FIRST])

    with pytest.raises(AddError, match="사진을 받을 수 없음.*404.*공개"):
        add_post(queue, "https://raw.githubusercontent.com/me/private/main/a.jpg", "비공개 저장소의 사진",
                 "2026-11-14T20:00:00+09:00", fetch=unreachable)

    assert read_queue(queue) == [FIRST]


def test_automatic_id_skips_ids_already_in_the_queue(tmp_path):
    queue = tmp_path / "queue.json"
    write_queue(queue, [{**FIRST, "id": "post-2"}])

    post = add_post(queue, "https://example.com/next.jpg", "다음 글",
                    "2026-11-14T20:00:00+09:00", fetch=fake_fetch(JPEG_START))

    assert post["id"] == "post-3"
    assert [p["id"] for p in read_queue(queue)] == ["post-2", "post-3"]


def test_chosen_id_is_used_and_a_duplicate_is_refused(tmp_path):
    queue = tmp_path / "queue.json"
    write_queue(queue, [FIRST])

    post = add_post(queue, "https://example.com/a.jpg", "글", "2026-11-14T20:00:00+09:00",
                    fetch=fake_fetch(JPEG_START), post_id="launch-day")
    assert post["id"] == "launch-day"

    with pytest.raises(AddError, match="이미 있는 id: first-post"):
        add_post(queue, "https://example.com/b.jpg", "글", "2026-11-14T20:00:00+09:00",
                 fetch=fake_fetch(JPEG_START), post_id="first-post")
    assert [p["id"] for p in read_queue(queue)] == ["first-post", "launch-day"]
