"""기업마당(bizinfo.go.kr) 지원사업 공고 API.

환경변수 BIZINFO_API_KEY 필요 (기업마당 > 오픈API 신청 후 발급되는 crtfcKey).
기존에 쓰던 키 그대로 사용 가능.
"""
import os
import datetime
import requests

API_URL = "https://www.bizinfo.go.kr/uss/rss/bizinfoApi.do"


def fetch(recent_days: int = 7, search_cnt: int = 500) -> list:
    key = os.environ.get("BIZINFO_API_KEY")
    if not key:
        raise RuntimeError("BIZINFO_API_KEY 환경변수가 없습니다")

    r = requests.get(
        API_URL,
        params={"crtfcKey": key, "dataType": "json", "searchCnt": search_cnt},
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    items = data.get("jsonArray", data if isinstance(data, list) else [])

    cutoff = datetime.date.today() - datetime.timedelta(days=recent_days)
    out = []
    for it in items:
        reg = (it.get("creatPnttm") or "")[:10]  # 등록일 YYYY-MM-DD
        try:
            if reg and datetime.date.fromisoformat(reg) < cutoff:
                continue
        except ValueError:
            pass
        out.append({
            "title": _strip(it.get("pblancNm")),
            "summary": _strip(it.get("bsnsSumryCn")),
            "url": "https://www.bizinfo.go.kr" + (it.get("pblancUrl") or ""),
            "deadline": _strip(it.get("reqstBeginEndDe")),
            # 소관기관 + 수행기관을 합쳐 기관명 매칭 필드로 사용
            "agency_field": f"{it.get('jrsdInsttNm','')} {it.get('excInsttNm','')}",
        })
    return out


def _strip(s):
    import re
    return re.sub(r"<[^>]+>", "", s or "").strip()
