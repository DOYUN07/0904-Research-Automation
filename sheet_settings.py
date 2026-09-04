"""구글 시트에서 설정(수신자·키워드·제외키워드) 읽기.

환경변수 SHEET_ID 필요 (시트 URL의 /d/ 와 /edit 사이 문자열).
시트는 "링크가 있는 모든 사용자 - 뷰어" 공유 상태여야 함.

시트 구성 (탭 이름 고정):
  수신자     : A열에 메일 주소 (1행부터, 헤더 없이)
  키워드     : A열 그룹명, B열 동의어(쉼표 구분) — 예: 시니어돌봄 | 시니어,돌봄,케어
  제외키워드 : A열에 제외 단어

탭이 없거나 읽기 실패 시 해당 항목은 기존 설정(config.yaml / MAIL_TO secret)을 그대로 사용.
"""
import os
import io
import csv
import requests

BASE = "https://docs.google.com/spreadsheets/d/{sid}/gviz/tq?tqx=out:csv&sheet={tab}"


def _read_tab(sid: str, tab: str) -> list:
    """탭을 CSV로 받아 행 리스트 반환. 실패 시 None."""
    try:
        r = requests.get(BASE.format(sid=sid, tab=tab), timeout=20)
        r.raise_for_status()
        if "text/csv" not in r.headers.get("Content-Type", ""):
            return None  # 비공개 시트 → 로그인 HTML이 옴
        return list(csv.reader(io.StringIO(r.content.decode("utf-8"))))
    except Exception:
        return None


def load() -> dict:
    """{recipients: [..]|None, keywords: {..}|None, excludes: [..]|None, notes: [..]}"""
    out = {"recipients": None, "keywords": None, "excludes": None, "notes": []}
    sid = os.environ.get("SHEET_ID", "").strip()
    if not sid:
        return out  # 시트 미연동 — 기존 방식 사용

    rows = _read_tab(sid, "수신자")
    if rows is None:
        out["notes"].append("시트 '수신자' 탭 읽기 실패 → MAIL_TO secret 사용")
    else:
        emails = [c.strip() for row in rows for c in row[:1] if "@" in c]
        if emails:
            out["recipients"] = emails

    rows = _read_tab(sid, "키워드")
    if rows is None:
        out["notes"].append("시트 '키워드' 탭 읽기 실패 → config.yaml 사용")
    else:
        kw = {}
        for row in rows:
            if not row or not row[0].strip():
                continue
            group = row[0].strip()
            words = [w.strip() for w in (row[1] if len(row) > 1 else "").split(",") if w.strip()]
            kw[group] = words or [group]
        if kw:
            out["keywords"] = kw

    rows = _read_tab(sid, "제외키워드")
    if rows is None:
        out["notes"].append("시트 '제외키워드' 탭 읽기 실패 → config.yaml 사용")
    else:
        ex = [row[0].strip() for row in rows if row and row[0].strip()]
        if ex:
            out["excludes"] = ex

    return out
