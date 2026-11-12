# AGENTS.md

## Agent skills

### Issue tracker

Issues live as local markdown files under `.scratch/<feature>/` in this repo. See `docs/agents/issue-tracker.md`.

### Triage labels

Default vocabulary, recorded as a `Status:` line in each issue file: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `CONTEXT.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.

## 제작기 영상 소재 기록

이 저장소의 개발 과정은 그대로 제작기 영상(`.scratch/making-of-video/`)의 소재가 된다. 기능 개발 단계를 하나 마칠 때마다, 그리고 실패하거나 방향을 바꿀 때마다 `.scratch/making-of-video/devlog.md`에 기록 규칙대로 항목을 추가하고, 에러 원문, 터미널 출력, 스크린샷을 `captures/`에 저장한다. 날짜와 기간은 적지 않는다.

## 비밀 정보 보호

토큰은 `.env`에만 둔다 (`.gitignore`에 있음). 커밋 전에 gitleaks가 스테이징된 변경을 검사해서 키·토큰이 있으면 커밋을 막는다. 새로 클론했으면 한 번 실행한다:

```
brew install gitleaks
git config core.hooksPath .githooks
```

`captures/`에 터미널 출력을 저장할 때 토큰이 섞이지 않게 한다. 훅이 막으면 우회(`--no-verify`)하지 말고 그 파일에서 토큰을 지운다.
