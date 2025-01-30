from email.mime.multipart import MIMEMultipart

import smtplib

import os
from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = os.getenv('SMTP_PORT', 587)

ENDPOINT = os.getenv('EMAIL')
APP_PASSWORD = os.getenv('APP_PASSWORD')

def send_smtp_email(msg: MIMEMultipart):
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.ehlo()

    except Exception as ex:
        raise Exception('Unexpected Error: SMTP server cannot be configured. Please see the .env file.') from ex

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()

        try:
            server.login(ENDPOINT, APP_PASSWORD)

        except smtplib.SMTPAuthenticationError as auth_error:
            raise Exception('SMTPAuthenticationError: Please see the .env file.') from auth_error
        
        except Exception as ex:
            raise Exception('Unexpected Error: Failed to login to the SMTP server. Please see the .env file.') from ex

        try:
            server.send_message(msg)

        except Exception as ex:
            raise Exception('Unexpected Error: Failed to send the email.') from ex
