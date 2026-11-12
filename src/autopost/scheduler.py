import json
from datetime import datetime

from autopost.errors import PublishError
from autopost.validation import problems


def run_due(queue_path, publisher, now):
    posts = json.loads(queue_path.read_text(encoding="utf-8"))
    for post in posts:
        if post.get("status") in ("posted", "failed"):
            continue
        found = problems(post)
        if found:
            post["status"] = "failed"
            post["error"] = "; ".join(found)
            continue
        if datetime.fromisoformat(post["scheduled_at"]) <= now:
            try:
                post["media_id"] = publisher.publish(post["image_url"], post["caption"])
                post["status"] = "posted"
            except PublishError as error:
                post["status"] = "failed"
                post["error"] = str(error)
    queue_path.write_text(json.dumps(posts, ensure_ascii=False, indent=2), encoding="utf-8")
