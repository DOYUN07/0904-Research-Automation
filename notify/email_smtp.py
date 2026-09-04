"""메일 발송 (Gmail SMTP 기준).

필요 환경변수:
  SMTP_USER : Gmail 주소
  SMTP_PASS : 앱 비밀번호 (구글 계정 > 보안 > 2단계 인증 > 앱 비밀번호)
  MAIL_TO   : 수신 주소 (미설정 시 SMTP_USER로 발송)
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.header import Header


def send(subject: str, body: str):
    user = os.environ["SMTP_USER"]
    pw = os.environ["SMTP_PASS"]
    to = os.environ.get("MAIL_TO", user)

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = user
    msg["To"] = to

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as s:
        s.login(user, pw)
        s.sendmail(user, [to], msg.as_string())
