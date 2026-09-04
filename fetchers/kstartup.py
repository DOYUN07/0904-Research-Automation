"""K-Startup 사업공고 API (공공데이터포털 데이터셋 15125364).

환경변수 DATA_GO_KR_KEY 필요 (data.go.kr 인증키, 활용신청 후 발급).
※ 엔드포인트 경로는 활용신청 페이지의 Swagger에서 최종 확인할 것
   (서비스명 kisedKstartupService 버전 표기가 변경될 수 있음).
"""
import os
import datetime
import requests

API_URL = "https://apis.data.go.kr/B552735/kisedKstartupService01/getAnnouncementInformation01"


def fetch(recent_days: int = 7, per_page: int = 100) -> list:
    key = os.environ.get("DATA_GO_KR_KEY")
    if not key:
        raise RuntimeError("DATA_GO_KR_KEY 환경변수가 없습니다")

    r = requests.get(
        API_URL,
        params={"serviceKey": key, "page": 1, "perPage": per_page, "returnType": "json"},
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    items = data.get("data", [])

    cutoff = datetime.date.today() - datetime.timedelta(days=recent_days)
    out = []
    for it in items:
        reg = (it.get("pbanc_rcpt_bgng_dt") or it.get("intg_pbanc_biz_nm") and "")
        # 등록일 필드가 스키마에 따라 다름 → 모집시작일 기준으로 최근성 판단
        start = (it.get("pbanc_rcpt_bgng_dt") or "")[:10].replace(".", "-")
        try:
            if start and datetime.date.fromisoformat(start) < cutoff:
                continue
        except ValueError:
            pass
        out.append({
            "title": (it.get("intg_pbanc_biz_nm") or it.get("biz_pbanc_nm") or "").strip(),
            "summary": (it.get("pbanc_ctnt") or "")[:300],
            "url": it.get("detl_pg_url") or "https://www.k-startup.go.kr",
            "deadline": it.get("pbanc_rcpt_end_dt") or "",
            "agency_field": "K-Startup",
        })
    return out
