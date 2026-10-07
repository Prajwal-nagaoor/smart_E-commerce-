import smtplib
import os

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465

EMAIL_USERNAME = os.getenv("EMAIL_USERNAME")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")


def send_email(to_email, subject, message):

    try:
        email = MIMEMultipart()

        email["From"] = EMAIL_USERNAME
        email["To"] = to_email
        email["Subject"] = subject

        email.attach(
            MIMEText(message, "plain")
        )

        # Gmail SSL connection
        with smtplib.SMTP_SSL(
            SMTP_SERVER,
            SMTP_PORT,
            timeout=30
        ) as server:

            server.login(
                EMAIL_USERNAME,
                EMAIL_PASSWORD
            )

            server.sendmail(
                EMAIL_USERNAME,
                to_email,
                email.as_string()
            )

        print("Email sent successfully")

        return True

    except Exception as e:

        print("Email sending failed:", repr(e))

        return False


# if __name__ == "__main__":

#     result = send_email(
#         "prajwalnaganoor6@gmail.com",
#         "Test Email",
#         "This is a test email from my FastAPI project."
#     )

#     print("Email result:", result)