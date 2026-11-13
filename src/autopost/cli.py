import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from autopost.adding import add_post
from autopost.errors import AddError, AuthError
from autopost.graph_api import GraphApiPublisher
from autopost.http import UrllibHttp, fetch_head
from autopost.scheduler import run_due

REQUIRED = ("IG_USER_ID", "IG_ACCESS_TOKEN")


def load_env(path=Path(".env")):
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            if value.strip():
                os.environ.setdefault(key.strip(), value.strip())


def add_command(argv, fetch):
    parser = argparse.ArgumentParser(prog="autopost add", description="공개 URL의 JPEG 사진으로 글 하나를 큐에 추가한다")
    parser.add_argument("image_url", help="인스타그램이 가져갈 수 있는 공개 JPEG 주소")
    parser.add_argument("--caption", required=True)
    parser.add_argument("--at", required=True, help="예약 시각, 시간대 포함 (예: 2026-11-14T20:00:00+09:00)")
    parser.add_argument("--id", dest="post_id", help="글 id (생략하면 post-N)")
    parser.add_argument("--queue", default="queue.json")
    args = parser.parse_args(argv)
    try:
        post = add_post(Path(args.queue), args.image_url, args.caption, args.at, fetch=fetch, post_id=args.post_id)
    except AddError as error:
        print(f"큐에 넣지 않음: {error}", file=sys.stderr)
        return 1
    print(f"{post['id']}: 큐에 추가됨 ({post['scheduled_at']})")
    print(f"다음: git add {args.queue} && git commit -m \"queue: {post['id']}\" && git push")
    return 0


def main(argv=None, fetch=fetch_head):
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] == "add":
        return add_command(argv[1:], fetch)
    queue_path = Path(argv[0] if argv else "queue.json")
    load_env()
    missing = [name for name in REQUIRED if not os.environ.get(name)]
    if missing:
        print(f".env에 값이 없음: {', '.join(missing)} (.env.example 참고)", file=sys.stderr)
        return 2

    publisher = GraphApiPublisher(
        user_id=os.environ["IG_USER_ID"],
        access_token=os.environ["IG_ACCESS_TOKEN"],
        http=UrllibHttp(),
        host=os.environ.get("IG_GRAPH_HOST") or "graph.facebook.com",
        version=os.environ.get("IG_API_VERSION") or "v27.0",
    )
    before = {p["id"]: p.get("status") for p in json.loads(queue_path.read_text(encoding="utf-8"))}
    try:
        run_due(queue_path, publisher, datetime.now(timezone.utc))
    except AuthError as error:
        print(f"토큰 문제로 중단 (글은 대기 상태로 남음): {error}", file=sys.stderr)
        print("Meta 대시보드에서 토큰을 새로 발급해 .env와 GitHub Secrets에 넣을 것", file=sys.stderr)
        return 3
    for post in json.loads(queue_path.read_text(encoding="utf-8")):
        if post.get("status") != before.get(post["id"]):
            detail = post.get("media_id") or post.get("error")
            print(f"{post['id']}: {post['status']} ({detail})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
