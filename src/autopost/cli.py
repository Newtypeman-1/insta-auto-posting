import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from autopost.graph_api import GraphApiPublisher
from autopost.http import UrllibHttp
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


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
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
    run_due(queue_path, publisher, datetime.now(timezone.utc))
    for post in json.loads(queue_path.read_text(encoding="utf-8")):
        if post.get("status") != before.get(post["id"]):
            detail = post.get("media_id") or post.get("error")
            print(f"{post['id']}: {post['status']} ({detail})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
