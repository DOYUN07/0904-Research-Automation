"""범용 게시판 스크래퍼.

config.yaml의 agencies[].board에 아래 3개를 채우면 동작:
  url            : 공고 목록 페이지 URL
  item_selector  : 목록의 행(row) 하나를 가리키는 CSS 선택자 (예: "table.board tbody tr")
  title_selector : 행 내부에서 제목 텍스트 (예: "td.title a")
  link_selector  : 행 내부에서 링크 <a> (보통 title_selector와 동일)

선택자 찾는 법: 크롬에서 목록 페이지 → F12 → 요소 우클릭 → Copy > Copy selector.
"""
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MorningBrief/1.0)"}


def fetch(board_cfg: dict, agency: str = "") -> list:
    url = board_cfg["url"]
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    r.encoding = r.apparent_encoding
    soup = BeautifulSoup(r.text, "html.parser")

    out = []
    for row in soup.select(board_cfg["item_selector"])[:30]:
        t = row.select_one(board_cfg["title_selector"])
        a = row.select_one(board_cfg.get("link_selector") or board_cfg["title_selector"])
        if not t:
            continue
        href = a.get("href", "") if a else ""
        out.append({
            "title": t.get_text(strip=True),
            "summary": "",
            "url": urljoin(url, href),
            "deadline": "",
            "agency_field": agency,
        })
    return out
