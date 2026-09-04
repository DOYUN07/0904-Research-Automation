#!/usr/bin/env python3
"""아침 공고 브리핑 — 기관별 키워드 선별 후 알림 발송.

계층 구조:
  1) 기업마당(bizinfo) API  → 대부분 기관의 지원사업 공고를 소관/수행기관명으로 매칭
  2) K-Startup API          → K-Startup 전용
  3) 개별 게시판 스크래퍼    → config에 url/selector가 채워진 기관만
"""
import os
import sys
import yaml
import datetime

from fetchers import bizinfo, kstartup, board
from report import build_report
from notify import send_all

HERE = os.path.dirname(os.path.abspath(__file__))


def load_config():
    with open(os.path.join(HERE, "config.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


def flatten_keywords(cfg) -> dict:
    """{그룹명: [단어...]} → 소문자 단어 → 그룹명 매핑."""
    kw = {}
    for group, words in cfg["keywords"].items():
        for w in words:
            kw[w.lower()] = group
    return kw


def match_keywords(text: str, kw_map: dict) -> list:
    """공고 제목/요약에서 매칭된 키워드 그룹 목록 반환."""
    t = (text or "").lower()
    hit = {group for word, group in kw_map.items() if word in t}
    return sorted(hit)


def run():
    cfg = load_config()
    kw_map = flatten_keywords(cfg)
    max_n = cfg.get("max_per_agency", 3)
    recent_days = cfg.get("recent_days", 7)

    # ── 1. 공고 수집 ──────────────────────────────
    errors = []
    biz_items = []
    try:
        biz_items = bizinfo.fetch(recent_days=recent_days)
    except Exception as e:
        errors.append(f"기업마당 API 오류: {e}")

    # ── 2. 기관별 선별 ────────────────────────────
    results = []  # [{name, status, items:[{title,url,keywords,deadline}]}]
    for ag in cfg["agencies"]:
        name = ag["name"]
        source = ag.get("source", "bizinfo")
        entry = {"name": name, "status": "ok", "items": []}

        try:
            if source == "kstartup":
                candidates = kstartup.fetch(recent_days=recent_days)
            elif ag.get("board", {}).get("url"):
                candidates = board.fetch(ag["board"], agency=name)
            else:
                # 기업마당 결과에서 기관명 부분일치
                needles = ag.get("match", [name])
                candidates = [
                    it for it in biz_items
                    if any(n in (it.get("agency_field") or "") for n in needles)
                ]
                # 게시판 미설정 + 기업마당 의존 기관 표시
                if not ag.get("match"):
                    entry["status"] = "unconfigured"
        except Exception as e:
            entry["status"] = "error"
            errors.append(f"{name}: {e}")
            results.append(entry)
            continue

        # 키워드 필터 → 상위 max_n건
        picked = []
        for it in candidates:
            hits = match_keywords(it.get("title", "") + " " + it.get("summary", ""), kw_map)
            if hits:
                it["keywords"] = hits
                picked.append(it)
            if len(picked) >= max_n:
                break
        entry["items"] = picked
        if not picked and entry["status"] == "ok":
            entry["status"] = "none"  # ← "공고 없음" 명시 대상
        results.append(entry)

    # ── 3. 리포트 생성 + 발송 ─────────────────────
    today = datetime.date.today().strftime("%Y-%m-%d (%a)")
    text = build_report(today, results, errors)
    print(text)
    send_all(subject=f"[아침 공고 브리핑] {today}", body=text)


if __name__ == "__main__":
    sys.exit(run())
