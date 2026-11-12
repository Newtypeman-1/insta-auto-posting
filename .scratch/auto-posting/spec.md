# Spec: 인스타그램 예약 자동 포스팅

Status: ready-for-human

## 하는 일

준비된 이미지와 캡션을 예약 큐에 넣어 두면, 정해진 시간이 지난 항목을 공식 Instagram Graph API로 게시한다.

## 결정

- 스택: Python 3.12+ (uv로 관리, 시스템 기본은 3.9라 쓰지 않음) + pytest (처음엔 TS를 골랐다가, 읽기 쉬운 쪽으로 사용자가 파이썬을 선택)
- 게시: Instagram Graph API의 2단계 흐름 — `POST /{ig-user-id}/media` (image_url, caption)으로 컨테이너 생성 → 상태 확인 → `POST /{ig-user-id}/media_publish`
- 실행: 크론 같은 스케줄러가 CLI를 주기적으로 실행하고, 실행될 때마다 예정 시간이 지난 항목만 게시
- 개발: TDD, 미리 합의한 seam에서만 테스트

## 큐 항목

이미지, 캡션, 예약 시각. 상태: 대기 / 게시됨(미디어 ID) / 실패(에러)

## 정한 기본값 (바꿀 수 있음)

- 이미지: 큐에 공개 URL을 직접 적는다. 로컬 파일 업로드는 나중에 따로
- 실패 처리: 실패한 글은 "failed"로 남기고 다시 시도하지 않는다. 고쳐서 상태를 지우면 다시 대기
- 검증에 걸린 글은 예약 시각과 관계없이 바로 failed
- 컨테이너 대기: 5초 간격, 최대 12번(60초)

## 사용법

```
cp .env.example .env        # IG_USER_ID, IG_ACCESS_TOKEN 채우기
cp queue.example.json queue.json
uv run autopost queue.json  # 크론으로 주기 실행
```

## 열린 질문

- 계정 준비: 비즈니스/크리에이터 계정, Meta 앱, 장기 토큰 (사용자가 직접 진행 중)
- 장기 토큰은 60일마다 만료된다. 갱신을 자동화할지
- 크론을 어디서 돌릴지 (이 Mac, 서버, GitHub Actions)
