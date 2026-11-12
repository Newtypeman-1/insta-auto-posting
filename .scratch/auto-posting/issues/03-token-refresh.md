# 03. 장기 토큰 갱신

Status: resolved
Type: task
Blocked by: 01

장기 토큰은 60일 뒤 만료된다. 만료 전에 갱신하는 방법을 정한다.

## Answer

토큰은 스스로 만료일을 조회할 수 없다(debug_token은 앱 토큰 필요). 대신 code 190이면 글을 대기로 두고 실행을 실패시켜 GitHub 실패 메일로 알게 함. 만료일은 Meta 대시보드의 configuration 미리보기에서 확인 가능. 알림이 오면 대시보드에서 토큰을 다시 발급해 .env와 GitHub Secrets를 바꾼다.
