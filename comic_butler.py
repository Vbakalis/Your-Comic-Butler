from email.mime import base
import aiohttp
import asyncio
import os
import logging
import smtplib

from email.mime.multipart import MIMEMultipart
from datetime import  datetime
from email.mime.text import MIMEText
from functools import wraps

from util import construct_catalogue_url, email_parts, url_date
from subscribers import fetch_emails, is_informed, is_everyone_informed


logging.basicConfig(
    format="%(asctime)s %(levelname)-10s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    handlers=[
        logging.FileHandler("log_file.log"),
        logging.StreamHandler()
    ],
)


def guard(fn):
    @wraps(fn)
    async def wrapper(*args, **kwargs):
        try:
            await fn(*args, **kwargs)
        except Exception as err:
            logging.error(
                "%s(*%s, **%s) Exception: %s", fn.__name__, args, kwargs, err,
            )
    return wrapper


async def month_changed():
    today = datetime.now()
    if today.day == 1:
        return True
    return False


async def send_email(receiver):
    logging.info("Sending Email to: %s...", receiver,)
    try:
        body, sender, title = email_parts("new_catalogue_email")
        sender_pass = os.getenv("EMAIL_PASSWORD")
        message = MIMEMultipart()
        message['From'] = sender
        message['To'] = receiver
        message['Subject'] = title
        message.attach(MIMEText(body, 'plain'))
        session = smtplib.SMTP('smtp.gmail.com', 587)
        session.starttls()
        session.login(sender, sender_pass)
        text = message.as_string()
        session.sendmail(sender, receiver, text)
        session.quit()
        logging.info("Email has been send")
    except ConnectionError:
        logging.error("Couldnt send email to: %s",receiver,)

async def new_catalogue():
    date_url = url_date()
    base_url = os.getenv("BASE_URL")
    cataloge_url = construct_catalogue_url(base_url, date_url)
    logging.info("Checking for the new Catalogue...")
    async with aiohttp.ClientSession() as session:
        async with session.get(cataloge_url) as resp:
            if resp.status == 200:
                return True
            return False

@guard
async def main():
    logging.info("The Comic Butler is starting...")
    has_month_changed = await month_changed()
    if has_month_changed:
        is_everyone_informed(0)
    new_catalog = await new_catalogue()
    emails = fetch_emails()
    informed = is_informed()[0]
    if new_catalog and not informed:
        for subscriber in emails:
            await send_email(subscriber)
        is_everyone_informed(1)
        logging.info("Found new catalogue")
    else:
        logging.info("New catalogue isn't out yet")
    logging.info("The Comic Butler is finished...")


loop = asyncio.get_event_loop()
loop.run_until_complete(main())




