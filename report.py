"""기관별 결과를 브리핑 텍스트로 변환."""

STATUS_NONE = "· 신규 공고 없음"
STATUS_UNCONF = "· (게시판 미설정 — config.yaml에 url/selector 입력 필요)"
STATUS_ERROR = "· 수집 오류 발생"


def build_report(today: str, results: list, errors: list, ongoing: list = None) -> str:
    lines = [f"■ 아침 공고 브리핑 — {today}", ""]

    with_items = [r for r in results if r["items"]]
    without = [r for r in results if not r["items"]]

    # 1) 공고 있는 기관 먼저
    if with_items:
        lines.append(f"▶ 키워드 매칭 공고 ({len(with_items)}개 기관)")
        for r in with_items:
            lines.append(f"\n[{r['name']}]")
            for it in r["items"]:
                kw = ",".join(it.get("keywords", []))
                dl = f" | 마감: {it['deadline']}" if it.get("deadline") else ""
                lines.append(f" - {it['title']}  ({kw}){dl}")
                lines.append(f"   {it['url']}")
    else:
        lines.append("▶ 오늘 키워드에 매칭된 공고가 없습니다.")

    # 2) 진행 중인 공고 — 이전 알림분 중 마감 전인 것 (마감 임박순)
    if ongoing:
        lines.append(f"\n▶ 진행 중인 공고 — 이전 알림, 아직 지원 가능 ({len(ongoing)}건)")
        for o in ongoing:
            dl = f" | 마감: {o['deadline']}" if o.get("deadline") else f" | {o['date']} 알림"
            lines.append(f" - [{o['agency']}] {o['title']}{dl}")
            if o.get("url"):
                lines.append(f"   {o['url']}")

    # 3) 공고 없는 기관 — 명시적으로 표기
    lines.append(f"\n▶ 공고 없음 / 미설정 ({len(without)}개 기관)")
    for r in without:
        tag = {"none": STATUS_NONE, "unconfigured": STATUS_UNCONF,
               "error": STATUS_ERROR}.get(r["status"], STATUS_NONE)
        lines.append(f" - {r['name']} {tag}")

    if errors:
        lines.append("\n⚠ 오류 로그")
        lines.extend(f" - {e}" for e in errors)

    return "\n".join(lines)
