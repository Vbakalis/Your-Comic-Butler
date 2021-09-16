import aiohttp
import asyncio
import calendar
import os
import json
import logging
import smtplib

from email.mime.multipart import MIMEMultipart
from datetime import date, datetime, timedelta
from dateutil import relativedelta
from email.mime.text import MIMEText
from functools import wraps

from util import construct_catalogue_url, get_next_month


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


async def month_changed():
    tomorrows_month = (datetime.today() + timedelta(days=1)).month
    tomorrows_month = calendar.month_name[tomorrows_month]
    todays_month =  await get_next_month()
    return True if tomorrows_month != todays_month else False

async def fetch_subs():
    with open("subscribers.json", "r") as subs:
        subs = subs.read()
    subscribers = json.loads(subs)
    return subscribers

async def email_parts():
    date_url = await url_date()
    todays_month = await get_next_month("%B")
    catalogue_url = await construct_catalogue_url(BASE_URL, date_url)
    with open("new_catalogue_email_parts.json", "r") as parts:
        parts = parts.read()
    json_email_parts = json.loads(parts)
    body = json_email_parts["parts"]["body"].format(link=catalogue_url, month=todays_month)
    sender = os.getenv("COMIC_BUTLER_EMAIL")
    title = json_email_parts["parts"]["subject"].format(month=todays_month)
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
    next_month_date = await get_next_month("%b%y")
    return next_month_date


async def new_catalogue():
    date_url = await url_date()
    cataloge_url = await construct_catalogue_url(BASE_URL, date_url)
    logging.info("Checking for the new Catalague...")
    async with aiohttp.ClientSession() as session:
        async with session.get(cataloge_url, verify_ssl=False) as resp:
            if resp.status == 200:
                logging.info("Found new catalogue")
                return True
            logging.info("New catalogue isn't out yet")
            return False

@guard
async def main():
    logging.info("The Comic Butler is starting...")
    new_catalog = await new_catalogue()
    subscribers = await fetch_subs()
    await send_email("vasilis.mbakalis@gmail.com")
    if new_catalog and not month_changed:
        for subscriber in subscribers["subs_info"]:
            await send_email(subscriber["email"])
    logging.info("The Comic Butler is finished...")


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
