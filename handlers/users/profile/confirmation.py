import secrets
import smtplib
from data.text import SUBJECT, BODY
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import GMAIL_ADDRESS
from config import GMAIL_APP_PASSWORD


def rand_code() -> str:
    return "".join(secrets.choice("0123456789") for _ in range(6))


def send_email(TO_ADDRESS):
    rand_cod = rand_code()
    msg = MIMEMultipart()
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = TO_ADDRESS
    msg["Subject"] = SUBJECT
    msg.attach(MIMEText(rand_cod + BODY, "plain", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, TO_ADDRESS, msg.as_string())

    print('Письмо отправлено!')
    return rand_cod