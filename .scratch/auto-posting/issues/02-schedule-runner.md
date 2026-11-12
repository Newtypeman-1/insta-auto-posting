# 02. 주기 실행 설정

Status: ready-for-human
Type: task
Blocked by: 01

크론(또는 launchd, GitHub Actions)으로 `uv run autopost queue.json`을 주기적으로 실행한다. 어디서 돌릴지 사용자와 정한다.

## Answer

GitHub Actions로 결정. `.github/workflows/autopost.yml` (15분마다, concurrency로 겹침 방지, 큐 상태를 다시 커밋). 남은 일: 사용자가 GitHub Secrets에 IG_ACCESS_TOKEN, IG_USER_ID 등록 → push → 수동 실행으로 확인.
