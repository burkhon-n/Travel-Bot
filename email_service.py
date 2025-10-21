import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config
from models import User

def send_email(to: User, subject: str, message: str):
        msg = MIMEMultipart()
        msg['From'] = Config.EMAIL
        msg['To'] = to.email
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'html'))
        server = smtplib.SMTP('smtp-mail.outlook.com', 587)
        server.starttls()
        server.login(Config.EMAIL, Config.EMAIL_PASS)
        text = msg.as_string()
        server.sendmail(Config.EMAIL, to.email, text)
        server.quit()

send_email(
        User(email="burkhon0207@gmail.com", telegram_id=123456789),
        "Test Email",
        "<h1>This is a test email from Travel Bot</h1><p>If you received this, the email service is working!</p>"
)