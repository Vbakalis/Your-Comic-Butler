import aiohttp
import asyncio
import os
import json
import logging
import smtplib

from sqlalchemy import create_engine,engine, MetaData, Table, Column, Integer, String
from email.mime.multipart import MIMEMultipart
from datetime import  datetime
from email.mime.text import MIMEText
from functools import wraps
from email.message import EmailMessage

from util import construct_catalogue_url, get_next_month
from subscribers import fetch_emails, is_informed, is_everyone_informed

BASE_URL = "https://www.previewsworld.com/"

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


# async def everyone_is_informed(informed):
#     os.environ["IS_INFORMED"] = str(informed)

async def month_changed():
    today = datetime.now()
    if today.day == 1:
        return True
    return False


async def email_parts():
    date_url = await url_date()
    todays_month = get_next_month("%B")
    catalogue_url = construct_catalogue_url(BASE_URL, date_url)
    with open("email_parts.json", "r") as parts:
        parts = parts.read()
    json_email_parts = json.loads(parts)
    body = json_email_parts["parts"]["new_catalogue_email"]["body"].format(
        link=catalogue_url, month=todays_month)
    sender = os.getenv("COMIC_BUTLER_EMAIL")
    title = json_email_parts["parts"]["new_catalogue_email"]["subject"].format(
        month=todays_month)
    return body, sender, title


async def send_email(receiver):
    logging.info("Sending Email to: %s...", receiver,)
    try:
        body, sender, title = await email_parts()
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


async def url_date():
    next_month_date = get_next_month("%b%y")
    return next_month_date


async def new_catalogue():
    date_url = await url_date()
    cataloge_url = construct_catalogue_url(BASE_URL, date_url)
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




