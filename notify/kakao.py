"""카카오톡 '나에게 보내기' — 기존 시스템과 동일 방식.

필요 환경변수:
  KAKAO_REST_KEY       : 카카오 앱 REST API 키
  KAKAO_REFRESH_TOKEN  : 리프레시 토큰 (액세스 토큰은 매회 갱신)

※ 리프레시 토큰도 약 2개월(59일) 무사용 시 만료됨.
   매일 실행되므로 실사용 중엔 자동 연장되지만, 워크플로가 오래 멈추면 재발급 필요.
"""
import os
import json
import requests

TOKEN_URL = "https://kauth.kakao.com/oauth/token"
MEMO_URL = "https://kapi.kakao.com/v2/api/talk/memo/default/send"


def _access_token() -> str:
    r = requests.post(TOKEN_URL, data={
        "grant_type": "refresh_token",
        "client_id": os.environ["KAKAO_REST_KEY"],
        "refresh_token": os.environ["KAKAO_REFRESH_TOKEN"],
    }, timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]


def send(body: str):
    # 카톡 텍스트 템플릿은 최대 200자 → 분할 발송
    token = _access_token()
    chunks = [body[i:i + 950] for i in range(0, len(body), 950)]
    for chunk in chunks[:5]:  # 과도한 분할 방지
        template = {
            "object_type": "text",
            "text": chunk[:1000],
            "link": {"web_url": "https://www.bizinfo.go.kr"},
        }
        r = requests.post(
            MEMO_URL,
            headers={"Authorization": f"Bearer {token}"},
            data={"template_object": json.dumps(template, ensure_ascii=False)},
            timeout=30,
        )
        r.raise_for_status()
