import json

import pytest

from autopost.cli import main

JPEG_START = b"\xff\xd8\xff\xe0\x00\x10JFIF"


@pytest.fixture
def empty_dir(tmp_path, monkeypatch):
    """실제 .env를 읽지 않도록 빈 폴더에서, 토큰 환경변수 없이 돌린다."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("IG_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("IG_USER_ID", raising=False)
    return tmp_path


def test_add_command_puts_the_post_in_the_queue(empty_dir, capsys):
    queue = empty_dir / "queue.json"
    queue.write_text("[]", encoding="utf-8")

    code = main(["add", "https://example.com/photo.jpg", "--caption", "두 번째 글 #autopost",
                 "--at", "2026-11-14T20:00:00+09:00", "--queue", str(queue)],
                fetch=lambda url: JPEG_START)

    assert code == 0
    assert json.loads(queue.read_text(encoding="utf-8"))[0]["image_url"] == "https://example.com/photo.jpg"
    assert "post-1" in capsys.readouterr().out


def test_add_command_explains_a_refusal(empty_dir, capsys):
    queue = empty_dir / "queue.json"
    queue.write_text("[]", encoding="utf-8")

    code = main(["add", "https://example.com/photo.png", "--caption", "글",
                 "--at", "2026-11-14T20:00:00+09:00", "--queue", str(queue)],
                fetch=lambda url: b"\x89PNG\r\n\x1a\n")

    assert code == 1
    assert "JPEG가 아님 (PNG로 보임)" in capsys.readouterr().err
    assert queue.read_text(encoding="utf-8") == "[]"


def test_posting_command_still_takes_a_queue_path(empty_dir, capsys):
    (empty_dir / "queue.json").write_text("[]", encoding="utf-8")

    assert main(["queue.json"]) == 2
    assert ".env에 값이 없음" in capsys.readouterr().err
