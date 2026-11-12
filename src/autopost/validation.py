import re
from datetime import datetime

CAPTION_LIMIT = 2200
HASHTAG_LIMIT = 30


def problems(post):
    """큐 항목이 인스타그램에 보낼 수 없는 이유 목록. 비어 있으면 보낼 수 있다."""
    found = []
    if not post.get("image_url"):
        found.append("이미지 URL이 없음")
    caption = post.get("caption", "")
    if len(caption) > CAPTION_LIMIT:
        found.append(f"캡션이 {CAPTION_LIMIT}자를 넘음 ({len(caption)}자)")
    hashtags = re.findall(r"#\w+", caption)
    if len(hashtags) > HASHTAG_LIMIT:
        found.append(f"해시태그가 {HASHTAG_LIMIT}개를 넘음 ({len(hashtags)}개)")
    try:
        scheduled_at = datetime.fromisoformat(post["scheduled_at"])
    except ValueError:
        found.append(f"예약 시각을 읽을 수 없음: {post['scheduled_at']}")
    else:
        if scheduled_at.tzinfo is None:
            found.append("예약 시각에 시간대가 없음 (예: 2026-11-04T20:00:00+09:00)")
    return found
