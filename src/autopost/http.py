import json
import urllib.error
import urllib.parse
import urllib.request


class UrllibHttp:
    """실제 네트워크로 요청을 보낸다. 에러 응답도 JSON 본문을 그대로 돌려준다."""

    def request(self, method, url, params):
        encoded = urllib.parse.urlencode(params)
        if method == "GET":
            req = urllib.request.Request(f"{url}?{encoded}", method="GET")
        else:
            req = urllib.request.Request(url, data=encoded.encode(), method=method)
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read())
        except urllib.error.HTTPError as error:
            return json.loads(error.read())


def fetch_head(url, size=16):
    """URL의 앞 몇 바이트만 받아 온다 (사진 형식 확인용). 못 받으면 OSError."""
    req = urllib.request.Request(url, headers={"Range": f"bytes=0-{size - 1}", "User-Agent": "autopost"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read(size)
