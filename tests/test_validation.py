from autopost.validation import problems


def valid_post(**overrides):
    post = {
        "id": "first",
        "image_url": "https://example.com/cat.jpg",
        "caption": "첫 자동 포스팅",
        "scheduled_at": "2026-11-04T11:00:00+00:00",
    }
    post.update(overrides)
    return post


def test_valid_post_has_no_problems():
    assert problems(valid_post()) == []


def test_post_without_image_is_rejected():
    post = valid_post()
    del post["image_url"]
    assert problems(post) == ["이미지 URL이 없음"]


def test_caption_over_2200_characters_is_rejected():
    assert problems(valid_post(caption="가" * 2201)) == ["캡션이 2200자를 넘음 (2201자)"]


def test_more_than_30_hashtags_is_rejected():
    caption = "오늘의 사진 " + " ".join(f"#태그{n}" for n in range(31))
    assert problems(valid_post(caption=caption)) == ["해시태그가 30개를 넘음 (31개)"]


def test_schedule_without_timezone_is_rejected():
    assert problems(valid_post(scheduled_at="2026-11-04T11:00")) == [
        "예약 시각에 시간대가 없음 (예: 2026-11-04T20:00:00+09:00)"
    ]


def test_unreadable_schedule_is_rejected():
    assert problems(valid_post(scheduled_at="내일 저녁")) == [
        "예약 시각을 읽을 수 없음: 내일 저녁"
    ]
