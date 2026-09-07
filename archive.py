"""날짜별 브리핑 아카이브.

실행 시마다:
  logs/YYYY-MM-DD.md  : 그날 브리핑 전문
  history.csv         : 매칭 공고 누적 (엑셀에서 바로 열림, utf-8-sig)
GitHub Actions에서 커밋 단계가 이 파일들을 저장소에 push함.
"""
import os
import csv
import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(HERE, "logs")
CSV_PATH = os.path.join(HERE, "history.csv")
CSV_HEADER = ["날짜", "기관", "공고명", "키워드", "마감", "링크"]


def load_seen() -> set:
    """history.csv에 이미 기록된 공고의 링크·(기관|제목) 집합 → 중복 제거용."""
    seen = set()
    if not os.path.exists(CSV_PATH):
        return seen
    with open(CSV_PATH, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row.get("링크"):
                seen.add(row["링크"])
            seen.add(f"{row.get('기관','')}|{row.get('공고명','')}")
    return seen


def _parse_end_date(deadline: str):
    """'2026-09-01 ~ 2026-09-30', '20260930' 등에서 마지막 날짜 추출. 실패 시 None."""
    import re
    text = deadline or ""
    dates = re.findall(r"(\d{4})[.\-/]?\s?(\d{2})[.\-/]?\s?(\d{2})", text)
    if dates:
        y, m, d = dates[-1]
        try:
            return datetime.date(int(y), int(m), int(d))
        except ValueError:
            pass
    # 연도 없는 표기: (~9/30), ~ 7.17 등 → 올해로 가정
    md = re.findall(r"~\s*(\d{1,2})[./](\d{1,2})", text)
    if md:
        m, d = md[-1]
        try:
            return datetime.date(datetime.date.today().year, int(m), int(d))
        except ValueError:
            pass
    return None


def load_ongoing(keep_days: int = 30) -> list:
    """이전에 알림했고 아직 유효한 공고 목록.

    - 마감일 파싱 가능: 오늘 이후면 유지
    - 마감일 없음/파싱 불가: 첫 알림일로부터 keep_days일 동안만 유지
    반환: [{date, agency, title, keywords, deadline, url, end}] (마감 임박순)
    """
    if not os.path.exists(CSV_PATH):
        return []
    today = datetime.date.today()
    out, seen_key = [], set()
    with open(CSV_PATH, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            key = row.get("링크") or f"{row.get('기관')}|{row.get('공고명')}"
            if key in seen_key:
                continue
            seen_key.add(key)
            end = _parse_end_date(row.get("마감", ""))
            if end is not None:
                if end < today:
                    continue  # 마감 지남
            else:
                try:
                    first = datetime.date.fromisoformat(row.get("날짜", ""))
                    if (today - first).days > keep_days:
                        continue  # 마감일 미상 → 30일 경과 시 제외
                except ValueError:
                    continue
            out.append({
                "date": row.get("날짜", ""),
                "agency": row.get("기관", ""),
                "title": row.get("공고명", ""),
                "keywords": row.get("키워드", ""),
                "deadline": row.get("마감", ""),
                "url": row.get("링크", ""),
                "end": end,
            })
    # 마감 임박순 정렬 (마감일 없는 건 뒤로)
    out.sort(key=lambda r: (r["end"] is None, r["end"] or datetime.date.max))
    return out


def save(text: str, results: list):
    today = datetime.date.today().isoformat()

    # 1) 그날 브리핑 전문
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(os.path.join(LOG_DIR, f"{today}.md"), "w", encoding="utf-8") as f:
        f.write(text + "\n")

    # 2) 누적 CSV (utf-8-sig → 엑셀 한글 깨짐 방지)
    new_file = not os.path.exists(CSV_PATH)
    with open(CSV_PATH, "a", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(CSV_HEADER)
        for r in results:
            for it in r["items"]:
                w.writerow([
                    today,
                    r["name"],
                    it.get("title", ""),
                    ",".join(it.get("keywords", [])),
                    it.get("deadline", ""),
                    it.get("url", ""),
                ])
