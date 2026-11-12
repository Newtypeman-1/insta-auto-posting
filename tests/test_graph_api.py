import pytest

from autopost.errors import AuthError, PublishError
from autopost.graph_api import GraphApiPublisher

BASE = "https://graph.facebook.com/v27.0"


class FakeHttp:
    """Meta 서버 대신 미리 정해 둔 응답을 돌려주고, 받은 요청을 기록한다."""

    def __init__(self, responses):
        self.responses = responses  # {(method, url): [응답, 응답, ...]}
        self.calls = []

    def request(self, method, url, params):
        self.calls.append((method, url, params))
        return self.responses[(method, url)].pop(0)


def make_publisher(http):
    return GraphApiPublisher(
        user_id="17841400000000000",
        access_token="test-token",
        http=http,
        sleep=lambda seconds: None,
    )


def test_publish_creates_container_waits_until_ready_then_publishes():
    http = FakeHttp({
        ("POST", f"{BASE}/17841400000000000/media"): [{"id": "container-1"}],
        ("GET", f"{BASE}/container-1"): [{"status_code": "FINISHED"}],
        ("POST", f"{BASE}/17841400000000000/media_publish"): [{"id": "media-99"}],
    })

    media_id = make_publisher(http).publish("https://example.com/cat.jpg", "첫 자동 포스팅")

    assert media_id == "media-99"
    assert http.calls == [
        ("POST", f"{BASE}/17841400000000000/media",
         {"image_url": "https://example.com/cat.jpg", "caption": "첫 자동 포스팅",
          "access_token": "test-token"}),
        ("GET", f"{BASE}/container-1",
         {"fields": "status_code", "access_token": "test-token"}),
        ("POST", f"{BASE}/17841400000000000/media_publish",
         {"creation_id": "container-1", "access_token": "test-token"}),
    ]


def test_publish_waits_while_instagram_is_still_fetching_the_image():
    http = FakeHttp({
        ("POST", f"{BASE}/17841400000000000/media"): [{"id": "container-1"}],
        ("GET", f"{BASE}/container-1"): [
            {"status_code": "IN_PROGRESS"},
            {"status_code": "IN_PROGRESS"},
            {"status_code": "FINISHED"},
        ],
        ("POST", f"{BASE}/17841400000000000/media_publish"): [{"id": "media-99"}],
    })

    media_id = make_publisher(http).publish("https://example.com/cat.jpg", "첫 자동 포스팅")

    assert media_id == "media-99"
    status_checks = [call for call in http.calls if call[0] == "GET"]
    assert len(status_checks) == 3


def test_container_error_stops_without_publishing():
    http = FakeHttp({
        ("POST", f"{BASE}/17841400000000000/media"): [{"id": "container-1"}],
        ("GET", f"{BASE}/container-1"): [{"status_code": "ERROR"}],
    })

    with pytest.raises(PublishError, match="컨테이너 처리 실패: ERROR"):
        make_publisher(http).publish("https://example.com/cat.jpg", "첫 자동 포스팅")

    assert not any(url.endswith("media_publish") for _, url, _ in http.calls)


def test_gives_up_when_container_never_finishes():
    http = FakeHttp({
        ("POST", f"{BASE}/17841400000000000/media"): [{"id": "container-1"}],
        ("GET", f"{BASE}/container-1"): [{"status_code": "IN_PROGRESS"}] * 20,
    })

    with pytest.raises(PublishError, match="컨테이너가 준비되지 않음"):
        make_publisher(http).publish("https://example.com/cat.jpg", "첫 자동 포스팅")

    status_checks = [call for call in http.calls if call[0] == "GET"]
    assert len(status_checks) == 12


def test_api_error_message_is_passed_on():
    http = FakeHttp({
        ("POST", f"{BASE}/17841400000000000/media"): [{
            "error": {
                "message": "Invalid OAuth access token - Cannot parse access token",
                "type": "OAuthException",
                "code": 190,
            }
        }],
    })

    with pytest.raises(PublishError, match="Invalid OAuth access token"):
        make_publisher(http).publish("https://example.com/cat.jpg", "첫 자동 포스팅")


def test_expired_token_raises_auth_error():
    http = FakeHttp({
        ("POST", f"{BASE}/17841400000000000/media"): [{
            "error": {
                "message": "Error validating access token: Session has expired",
                "type": "OAuthException",
                "code": 190,
            }
        }],
    })

    with pytest.raises(AuthError, match="Session has expired"):
        make_publisher(http).publish("https://example.com/cat.jpg", "첫 자동 포스팅")
