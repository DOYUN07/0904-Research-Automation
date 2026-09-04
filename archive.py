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
