"""범용 게시판 스크래퍼 (v2 — 자동 모드 지원).

config.yaml의 agencies[].board 설정:
  url           : 공고 목록 페이지 URL (필수)
  link_contains : 상세 링크에 반드시 포함될 문자열 (권장 — 예: "/home/2-2/")
  min_title_len : 제목 최소 길이 (기본 12자 — 메뉴 링크 걸러냄)
  item_selector / title_selector / link_selector : (선택) CSS 선택자 수동 지정

자동 모드 원리: 페이지의 모든 링크 중
  ① 제목이 충분히 길고 ② 같은 사이트 내부 링크이며 ③ 링크에 4자리 이상
  숫자(게시물 번호)가 포함된 것만 공고 후보로 수집.
  네비게이션 메뉴 오탐은 이후 키워드 필터에서 대부분 걸러짐.
행 주변 텍스트에서 '2026-09-03 ~ 2026-09-23' 형태의 기간을 찾아 마감으로 기록.
"""
import re
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"}

DATE_RANGE = re.compile(
    r"(\d{4}[.\-/]\s?\d{1,2}[.\-/]\s?\d{1,2}[^~]{0,12}~\s?[^0-9]{0,6}\d{4}[.\-/]\s?\d{1,2}[.\-/]\s?\d{1,2})"
)


def fetch(board_cfg: dict, agency: str = "") -> list:
    url = board_cfg["url"]
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    r.encoding = r.apparent_encoding
    soup = BeautifulSoup(r.text, "html.parser")

    if board_cfg.get("item_selector"):
        return _selector_mode(soup, board_cfg, url, agency)
    return _auto_mode(soup, board_cfg, url, agency)


def _auto_mode(soup, cfg, url, agency):
    host = urlparse(url).netloc
    min_len = int(cfg.get("min_title_len", 12))
    contains = cfg.get("link_contains")
    out, seen = [], set()

    for a in soup.find_all("a", href=True):
        title = a.get_text(" ", strip=True)
        href = a["href"]
        if len(title) < min_len:
            continue
        if href.startswith(("javascript", "#", "mailto")):
            continue
        full = urljoin(url, href)
        if urlparse(full).netloc != host:
            continue  # 외부 링크 제외
        if contains:
            if contains not in full:
                continue
        elif not re.search(r"\d{4,}", full):
            continue  # 게시물 번호(4자리+) 없는 링크는 메뉴일 가능성 높음
        if full in seen:
            continue
        seen.add(full)

        # 링크가 속한 행(tr/li 등) 텍스트에서 신청기간 추출
        deadline = ""
        parent = a
        for _ in range(4):
            parent = parent.parent
            if parent is None:
                break
            m = DATE_RANGE.search(parent.get_text(" ", strip=True))
            if m:
                deadline = re.sub(r"\s+", " ", m.group(1))
                break

        out.append({
            "title": title,
            "summary": "",
            "url": full,
            "deadline": deadline,
            "agency_field": agency,
        })
        if len(out) >= 40:
            break
    return out


def _selector_mode(soup, cfg, url, agency):
    out = []
    for row in soup.select(cfg["item_selector"])[:30]:
        t = row.select_one(cfg["title_selector"])
        a = row.select_one(cfg.get("link_selector") or cfg["title_selector"])
        if not t:
            continue
        href = a.get("href", "") if a else ""
        m = DATE_RANGE.search(row.get_text(" ", strip=True))
        out.append({
            "title": t.get_text(strip=True),
            "summary": "",
            "url": urljoin(url, href),
            "deadline": re.sub(r"\s+", " ", m.group(1)) if m else "",
            "agency_field": agency,
        })
    return out
