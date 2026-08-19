import smtplib
from email.utils import make_msgid, formatdate

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import GMAIL_ADDRESS
from config import GMAIL_APP_PASSWORD

DEVELOPER_EMAIL = GMAIL_ADDRESS

def send_bug_report(user_id: int, user_name: str | None, bug_text: str) :
    subject = f"FALCON GROP - баг-репорт от пользователя {user_id}"
    body = (
            f"Пользователь:  {user_name} (tg_id: {user_id})\n\n"
            f"Текст сообщения\n{bug_text}"
    )

    msg = MIMEMultipart()
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = DEVELOPER_EMAIL
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid()
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(DEVELOPER_EMAIL, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, DEVELOPER_EMAIL, msg.as_string())