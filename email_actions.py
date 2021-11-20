import aiohttp
import asyncio
import email
import imaplib
import mailbox
import os
import logging
import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from comic_butler import email_parts
from subscribers import fetch_emails, add_subscriber_to_db
logging.basicConfig(
    format="%(asctime)s %(levelname)-10s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    handlers=[
        logging.FileHandler("log_add_sub.log"),
        logging.StreamHandler()
    ],
)



async def send_verification_email(subscriber):
    logging.info("Sending Email to: %s...", subscriber,)
    try:
        body, sender, title = await email_parts("welcome_email")
        sender_pass = os.getenv("EMAIL_PASSWORD")
        message = MIMEMultipart()
        message['From'] = sender
        message['To'] = subscriber
        message['Subject'] = title
        message.attach(MIMEText(body, 'plain'))
        session = smtplib.SMTP('smtp.gmail.com', 587)
        session.starttls()
        session.login(sender, sender_pass)
        text = message.as_string()
        session.sendmail(sender, subscriber, text)
        session.quit()
        logging.info("Email has been send")
    except ConnectionError:
        logging.error("Couldnt send email to: %s", subscriber,)

async def check_inbox():
    cb_email = os.getenv("COMIC_BUTLER_EMAIL")
    password = os.getenv("EMAIL_PASSWORD")

    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    mail.login(cb_email, password)
    mail.list()
    mail.select('inbox')
    result, data = mail.uid('search', None, "UNSEEN")
    i = len(data[0].split())
    for new_email in range(i):
        latest_email_uid = data[0].split()[new_email]
        result, email_data = mail.uid('fetch', latest_email_uid, '(RFC822)')
        raw_email = email_data[0][1]
        raw_email_string = raw_email.decode('utf-8')
        email_message = email.message_from_string(raw_email_string)

        email_from = str(email.header.make_header(
            email.header.decode_header(email_message['From'])))
        email_to = str(email.header.make_header(
            email.header.decode_header(email_message['To'])))
        subject = str(email.header.make_header(
            email.header.decode_header(email_message['Subject'])))
        print(subject, email_from)
        if "subscribe" in subject and not await is_email_in_db(email_from):
            logging.info("New subscriber has been found %s",email_from)
            await send_verification_email(email_from)
            add_subscriber_to_db(await extract_subsriber_email(email_from))

async def extract_subsriber_email(subscriber):
    email = subscriber.split("<")[1].split(">")[0]
    name = subscriber.split("<")[0].split(">")[0]
    firstname = name.split(" ")[0]
    lastname = name.split(" ")[1]
    return email, firstname, lastname

async def is_email_in_db(email_from):
    if email_from not in fetch_emails():
        return False
    return True

async def main():
    await check_inbox()


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
