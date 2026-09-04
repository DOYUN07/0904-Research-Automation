"""메일 발송 (Gmail SMTP 기준).

필요 환경변수:
  SMTP_USER : Gmail 주소 (발신 계정)
  SMTP_PASS : 앱 비밀번호
  MAIL_TO   : 수신 주소 — 여러 명이면 쉼표로 구분
              예: kim@company.co.kr, lee@company.co.kr, park@gmail.com
              미설정 시 SMTP_USER 본인에게 발송.
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.header import Header


def send(subject: str, body: str, recipients=None):
    user = os.environ["SMTP_USER"]
    pw = os.environ["SMTP_PASS"]
    if recipients is None:  # 시트 미연동 시 MAIL_TO secret 사용
        raw = os.environ.get("MAIL_TO") or user
        recipients = [a.strip() for a in raw.split(",") if a.strip() and "@" in a]
    recipients = [a for a in recipients if "@" in a]
    if not recipients:
        recipients = [user]

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = user
    msg["To"] = ", ".join(recipients)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as s:
        s.login(user, pw)
        s.sendmail(user, recipients, msg.as_string())
