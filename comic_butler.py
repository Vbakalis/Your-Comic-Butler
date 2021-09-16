from email.mime.multipart import MIMEMultipart
from datetime import date, datetime, timedelta
from dateutil import relativedelta
from email.mime.text import MIMEText
from functools import wraps

import aiohttp
import asyncio
import calendar
import os
import json
import logging
import smtplib


LOG_FILENAME = "log_file.log"

BASE_URL = "https://www.previewsworld.com/"

logging.basicConfig(
    format="%(asctime)s %(levelname)-10s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    handlers=[
        logging.FileHandler(LOG_FILENAME),
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
    return True if tomorrows_month != TODAYS_MONTH else False

async def fetch_subs():
    with open("subscribers.json", "r") as subs:
        subs = subs.read()
    subscribers = json.loads(subs)
    return subscribers

async def email_parts():
    with open("new_catalogue_email_parts.json", "r") as parts:
        parts = parts.read()
    json_email_parts = json.loads(parts)
    body = json_email_parts["parts"]["body"].format(link=CATALOGUE_URL)
    sender = os.getenv("COMIC_BUTLER_EMAIL")
    title = json_email_parts["parts"]["subject"].format(month=TODAYS_MONTH)
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
    today = date.today()
    next_month_date = today + relativedelta.relativedelta(months=1)
    global TODAYS_MONTH
    TODAYS_MONTH = today.strftime("%B")
    next_month_date = next_month_date.strftime("%b%y")
    return next_month_date


async def new_catalogue():
    date_url = await url_date()
    global CATALOGUE_URL
    CATALOGUE_URL = f"{BASE_URL}Catalog?batch={date_url}"
    logging.info("Checking for the new Catalague...")
    async with aiohttp.ClientSession() as session:
        async with session.get(CATALOGUE_URL, verify_ssl=False) as resp:
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
    if new_catalog and not month_changed:
        for subscriber in subscribers["subs_info"]:
            await send_email(subscriber["email"])
    logging.info("The Comic Butler is finished...")


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
