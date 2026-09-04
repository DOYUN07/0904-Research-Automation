"""알림 발송 디스패처.

채널은 환경변수 NOTIFY_CHANNELS로 제어 (쉼표 구분: "kakao,email").
미설정 시 콘솔 출력만 수행 → GitHub Actions 로그에서 확인 가능.
채널 확정 후 secrets만 추가하면 코드 수정 없이 활성화됨.
"""
import os


def send_all(subject: str, body: str):
    channels = [c.strip() for c in os.environ.get("NOTIFY_CHANNELS", "").split(",") if c.strip()]
    if not channels:
        print("\n(NOTIFY_CHANNELS 미설정 — 콘솔 출력만 수행)")
        return
    for ch in channels:
        try:
            if ch == "kakao":
                from . import kakao
                kakao.send(body)
            elif ch == "email":
                from . import email_smtp
                email_smtp.send(subject, body)
            else:
                print(f"알 수 없는 채널: {ch}")
        except Exception as e:
            print(f"[{ch}] 발송 실패: {e}")
