# 아침 공고 브리핑 (gov-morning-brief)

매일 08:00(KST)에 34개 기관의 지원사업 공고를 키워드로 선별해 카카오톡/메일로 발송.
공고가 없는 기관은 "신규 공고 없음"으로 명시.

## 구조 (3계층)
1. **기업마당 API** — 대부분 기관의 지원사업 공고가 여기 집계됨. 소관/수행기관명으로 매칭 (기본)
2. **K-Startup API** — 전용 엔드포인트 (data.go.kr 인증키 필요)
3. **개별 게시판 스크래퍼** — 기업마당에 안 잡히는 기관만. config.yaml의 board에 url/선택자 입력 시 자동 활성화

## 설정 순서
1. GitHub 저장소 생성 → 이 폴더 업로드
2. Settings > Secrets and variables > Actions에 등록:
   - `BIZINFO_API_KEY` (필수, 기존 키 재사용)
   - `DATA_GO_KR_KEY` (K-Startup용 — data.go.kr에서 "창업진흥원_K-Startup 조회서비스" 활용신청)
   - `NOTIFY_CHANNELS` — 채널 확정 후 `kakao` / `email` / `kakao,email` 입력. 비워두면 Actions 로그로만 확인
3. Actions 탭 > morning-brief > Run workflow로 수동 테스트

## 게시판 기관 추가법
크롬에서 해당 기관 공고 목록 → F12 → 행 요소 우클릭 → Copy selector
→ config.yaml의 board에 url / item_selector / title_selector 입력

## 운영 시 조정 포인트
- `keywords`: '인증', '재난' 등 짧은 단어는 오탐이 많으면 구체화
- `recent_days`: 기본 7일. 매일 실행이면 2~3일로 줄여 중복 감소 가능
- K-Startup 엔드포인트 경로는 활용신청 후 Swagger에서 최종 확인 (버전 표기 변경 가능성)
