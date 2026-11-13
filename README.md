# autopost: 인스타그램 예약 자동 포스팅

공개된 주소에 있는 JPEG 사진과 캡션을 예약 큐(`queue.json`)에 넣어 두면, GitHub Actions가 15분마다 큐를 확인해서 예약 시각이 지난 글을 인스타그램에 올린다. 서버가 필요 없고, 내 컴퓨터가 꺼져 있어도 돈다.

- 공식 Instagram Graph API만 쓴다. 비밀번호 로그인이나 화면 자동 조작은 하지 않는다.
- 게시는 3단계다: 컨테이너 생성 → 인스타그램이 사진을 다 가져갈 때까지 상태 확인 → 게시.
- 같은 글을 두 번 올리지 않는다. 실패한 글은 다시 보내지 않고 이유를 큐에 적는다.
- 토큰이 만료되면 글은 대기 상태로 두고 실행을 실패시킨다. GitHub이 메일로 알려 준다.

## 시작하기 전에 알아 둘 것

- **사진은 JPEG만 된다.** 인스타그램 게시 API는 JPEG만 받는다. PNG, WebP, HEIC는 JPEG로 바꿔서 올려야 한다.
- **사진은 누구나 열 수 있는 공개 주소에 있어야 한다.** 인스타그램이 그 주소로 가서 사진을 직접 가져간다. 비공개 저장소의 raw 주소처럼 로그인이 필요한 주소는 안 된다.
- **예약 시각이 밀릴 수 있다.** GitHub의 예약 실행(`schedule`)은 늦어지거나 건너뛰는 일이 흔하다. 몇 시간씩 밀리기도 한다. 정확한 시각이 중요하면 [바로 실행하기](#바로-실행하기)나 [내 컴퓨터에서 정기 실행하기](#내-컴퓨터에서-정기-실행하기)를 쓴다.
- **인스타그램 하루 게시 한도는 24시간에 100개다.**

## 준비물

- 인스타그램 **프로페셔널 계정**(비즈니스 또는 크리에이터). 개인 계정은 API를 쓸 수 없다. 전환하면 계정이 공개로 바뀐다.
- Meta 개발자 계정
- GitHub 계정, `git`, [`uv`](https://docs.astral.sh/uv/), 그리고 선택 사항으로 [`gh`](https://cli.github.com/)

## 설치

### 1. 저장소를 내 계정으로 가져오기

이 저장소를 내 계정으로 복사한다. **포크했다면 예약 실행이 꺼져 있다.** GitHub는 포크한 저장소의 예약 워크플로를 기본으로 꺼 둔다. 저장소의 **Actions** 탭에서 워크플로를 켠다.

```bash
git clone https://github.com/<내-계정>/<저장소>.git
cd <저장소>
uv sync
```

`queue.json`에 원래 저장소의 게시 기록이 들어 있다면 빈 큐로 바꾼다.

```bash
echo '[]' > queue.json
```

### 2. Meta 앱에서 토큰 받기

1. [Meta for Developers](https://developers.facebook.com/)에서 앱을 만든다.
2. 앱 대시보드에서 Instagram API 설정으로 들어간다. 새 앱은 **API setup with unified login** 방식이 기본이다. 비즈니스 포트폴리오를 먼저 만들라고 하면 만든다.
   - 예전 문서에 나오는 "API setup with Instagram login" 메뉴는 새 앱에서는 보이지 않을 수 있다.
3. 프로페셔널 인스타 계정을 연결하고, **System-user access token**을 발급받는다. 게시 권한이 들어 있어야 한다.

Meta 대시보드의 메뉴 이름과 위치는 자주 바뀐다. 화면이 이 설명과 다르면 Meta 공식 문서의 Instagram Content Publishing 항목을 기준으로 한다.

### 3. 인스타 계정 ID 찾기

Unified Login 토큰으로 `/me`를 조회하면 인스타 계정이 아니라 시스템 사용자가 나온다. 인스타 계정 ID는 아래처럼 조회한다.

```bash
export IG_ACCESS_TOKEN='발급받은 토큰'
curl -s "https://graph.facebook.com/v27.0/me/assigned_instagram_accounts?access_token=$IG_ACCESS_TOKEN"
```

나온 `id`가 `IG_USER_ID`다. 게시 권한이 살아 있는지는 게시 한도로 확인한다.

```bash
curl -s "https://graph.facebook.com/v27.0/<IG_USER_ID>/content_publishing_limit?access_token=$IG_ACCESS_TOKEN"
```

`quota_usage`(오늘 쓴 개수)와 `quota_total: 100`이 나오면 된다.

### 4. 토큰을 GitHub Secrets에 넣기

저장소의 **Settings → Secrets and variables → Actions**에 `IG_ACCESS_TOKEN`과 `IG_USER_ID`를 넣는다. `gh`가 있으면:

```bash
gh secret set IG_ACCESS_TOKEN
gh secret set IG_USER_ID
```

내 컴퓨터에서도 돌리려면 `.env.example`을 `.env`로 복사해서 같은 값을 채운다. `.env`는 `.gitignore`에 있어 커밋되지 않는다.

**토큰은 절대 커밋하지 않는다.** 커밋 전에 토큰을 검사하는 훅을 켜 두기를 권한다.

```bash
brew install gitleaks
git config core.hooksPath .githooks
```

## 글 올리기

### 1. 큐에 글 추가하기

```bash
uv run autopost add https://example.com/photo.jpg \
  --caption "두 번째 글 #autopost" \
  --at "2026-11-14T20:00:00+09:00"
```

- `--at`에는 **반드시 시간대를 붙인다** (`+09:00`). 시간대가 없는 시각은 서울 시각인지 서버 시각인지 알 수 없어서 거절한다.
- 캡션은 2200자, 해시태그는 30개까지다.
- 사진 주소는 큐에 넣기 전에 직접 확인한다. 확장자가 아니라 파일 앞부분을 보고 JPEG인지 판단한다. JPEG가 아니거나 주소가 열리지 않으면 이유를 출력하고 큐에 넣지 않는다.
- 글 id는 `post-2`처럼 자동으로 붙는다. 직접 정하려면 `--id launch-day`를 쓴다.

큐를 직접 고쳐도 된다. 형식은 `queue.example.json`을 본다.

### 2. 커밋하고 푸시하기

```bash
git pull
git add queue.json
git commit -m "queue: post-2"
git push
```

글을 올리고 나면 봇이 `queue.json`에 결과를 적어 커밋한다. 그래서 푸시하기 전에 `git pull`을 먼저 한다.

### 3. 결과 확인하기

`git pull` 다음에 `queue.json`에서 그 글을 본다.

| `status` | 뜻 |
|---|---|
| 없음 | 대기 중 (예약 시각 전이거나 아직 실행되지 않음) |
| `posted` | 게시됨. `media_id`가 함께 적힌다 |
| `failed` | 실패. `error`에 이유가 적힌다. 실패한 글은 다시 보내지 않으니, 고쳐서 새 id로 다시 넣는다 |

## 바로 실행하기

예약 시각이 지났는데 아직 안 올라갔다면 직접 실행한다.

```bash
gh workflow run autopost.yml
```

또는 저장소의 **Actions → autopost → Run workflow**를 누른다.

## 내 컴퓨터에서 정기 실행하기

게시 명령은 GitHub 밖에서도 그대로 돈다. `.env`를 채웠다면:

```bash
uv run autopost queue.json
```

cron에 걸면 예약 시각이 정확해진다. 대신 컴퓨터가 켜져 있어야 하고, 바뀐 `queue.json`은 직접 커밋해야 한다. GitHub Actions와 동시에 쓰면 두 곳에서 같은 큐를 돌리게 되니 하나만 쓴다.

## 토큰이 만료되면

Actions 실행이 실패로 끝나고, 로그에 이렇게 나온다.

```
토큰 문제로 중단 (글은 대기 상태로 남음): Invalid OAuth access token - Cannot parse access token (code 190)
```

글은 실패로 처리되지 않고 대기 상태로 남아 있다. Meta 대시보드에서 토큰을 새로 발급해 GitHub Secrets(와 `.env`)에 넣으면 다음 실행 때 올라간다.

## 개발

```bash
uv run pytest
```

테스트는 진짜 인스타그램 대신 요청을 기록하는 가짜 게시기와 가짜 HTTP로 돈다. 네트워크도 토큰도 필요 없다.

| 파일 | 하는 일 |
|---|---|
| `src/autopost/scheduler.py` | 큐를 읽고 예약 시각이 지난 글을 게시, 상태 기록 |
| `src/autopost/graph_api.py` | 컨테이너 → 상태 확인 → 게시 |
| `src/autopost/validation.py` | 보내기 전에 거르는 규칙 (이미지, 2200자, 해시태그 30개, 시간대) |
| `src/autopost/adding.py` | `autopost add`: JPEG 확인 후 큐에 추가 |
| `.github/workflows/autopost.yml` | 15분마다 실행, 한 번에 하나만 |
