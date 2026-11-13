import json

from autopost.errors import AddError
from autopost.validation import problems

JPEG_MAGIC = b"\xff\xd8\xff"
OTHER_FORMATS = {b"\x89PNG": "PNG", b"GIF8": "GIF", b"RIFF": "WebP"}


def image_problem(head):
    """URL에서 받은 앞부분이 JPEG가 아니면 그 이유. 인스타그램 게시 API는 JPEG만 받는다."""
    if head.startswith(JPEG_MAGIC):
        return None
    seen = next((name for magic, name in OTHER_FORMATS.items() if head.startswith(magic)), None)
    if seen is None and head[4:12] in (b"ftypheic", b"ftypheix", b"ftypmif1"):
        seen = "HEIC"
    return f"JPEG가 아님 ({seen}로 보임)" if seen else "JPEG가 아님"


def add_post(queue_path, image_url, caption, scheduled_at, fetch, post_id=None):
    """공개 URL의 사진으로 글 하나를 큐에 대기 상태로 추가한다. 넣을 수 없으면 AddError, 큐는 그대로."""
    posts = json.loads(queue_path.read_text(encoding="utf-8"))
    taken = {p["id"] for p in posts}
    if post_id in taken:
        raise AddError(f"이미 있는 id: {post_id}")
    if post_id is None:
        n = len(posts) + 1
        while f"post-{n}" in taken:
            n += 1
        post_id = f"post-{n}"
    post = {
        "id": post_id,
        "image_url": image_url,
        "caption": caption,
        "scheduled_at": scheduled_at,
    }
    found = problems(post)
    if found:
        raise AddError("; ".join(found))
    try:
        head = fetch(image_url)
    except OSError as error:
        raise AddError(f"사진을 받을 수 없음 ({error}). 인스타그램이 가져갈 수 있게 누구나 열 수 있는 공개 주소여야 함") from error
    problem = image_problem(head)
    if problem:
        raise AddError(problem)
    posts.append(post)
    queue_path.write_text(json.dumps(posts, ensure_ascii=False, indent=2), encoding="utf-8")
    return post
