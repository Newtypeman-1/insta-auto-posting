import time

from autopost.errors import AuthError, PublishError


class GraphApiPublisher:
    """Instagram Graph API로 이미지 한 장을 게시한다.

    인스타그램은 바로 게시하지 않는다. 먼저 미디어 컨테이너를 만들고,
    인스타그램이 이미지를 다 받아 갈 때까지 기다린 뒤에 그 컨테이너를 게시한다.
    """

    def __init__(self, user_id, access_token, http, host="graph.facebook.com",
                 version="v27.0", sleep=time.sleep):
        self.user_id = user_id
        self.access_token = access_token
        self.http = http
        self.base = f"https://{host}/{version}"
        self.sleep = sleep
        self.poll_seconds = 5
        self.max_status_checks = 12

    def publish(self, image_url, caption):
        container = self._call("POST", f"{self.user_id}/media",
                               {"image_url": image_url, "caption": caption})
        self._wait_until_ready(container["id"])
        published = self._call("POST", f"{self.user_id}/media_publish",
                               {"creation_id": container["id"]})
        return published["id"]

    def _wait_until_ready(self, container_id):
        for _ in range(self.max_status_checks):
            status = self._call("GET", container_id, {"fields": "status_code"})
            if status["status_code"] == "FINISHED":
                return
            if status["status_code"] != "IN_PROGRESS":
                raise PublishError(f"컨테이너 처리 실패: {status['status_code']}")
            self.sleep(self.poll_seconds)
        waited = self.poll_seconds * self.max_status_checks
        raise PublishError(f"컨테이너가 준비되지 않음 ({waited}초 기다림)")

    def _call(self, method, path, params):
        body = self.http.request(method, f"{self.base}/{path}",
                                 {**params, "access_token": self.access_token})
        if "error" in body:
            error = body["error"]
            if error.get("code") == 190:
                raise AuthError(f"{error.get('message')} (code 190)")
            raise PublishError(f"{error.get('message')} (code {error.get('code')})")
        return body
