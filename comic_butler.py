import aiohttp
import asyncio
import calendar
import os
import json
import logging
import smtplib

from email.mime.multipart import MIMEMultipart
from datetime import  datetime, timedelta
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


async def everyone_is_informed(informed):
    with open("subscribers.json", "r") as jsonFile:
        data = json.load(jsonFile)
    data["is_informed"] = informed
    with open("subscribers.json", "w") as jsonFile:
        json.dump(data, jsonFile, indent=4)

async def month_changed():
    tomorrows_month = (datetime.today() + timedelta(days=1)).month
    tomorrows_month = calendar.month_name[tomorrows_month]
    todays_month = get_next_month("%B")
    return True if tomorrows_month != todays_month else False


async def fetch_subs():
    with open("subscribers.json", "r") as subs:
        subs = subs.read()
    subscribers = json.loads(subs)
    return subscribers


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
    if not has_month_changed:
        await everyone_is_informed(False)
    new_catalog = await new_catalogue()
    subscribers = await fetch_subs()
    informed = subscribers["is_informed"]
    if new_catalog and not informed:
        for subscriber in subscribers["subs_info"]:
            await send_email(subscriber["email"])
        await everyone_is_informed(True)
        logging.info("Found new catalogue")
    else:
        logging.info("New catalogue isn't out yet")
    logging.info("The Comic Butler is finished...")


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
