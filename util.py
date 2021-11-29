import os
import json

from datetime import date
from email.mime import base
from dateutil import relativedelta


def construct_catalogue_url(base_url, date_url):
    return f"{base_url}Catalog?batch={date_url}"


def get_next_month(strftime):
    today = date.today()
    next_month = today + relativedelta.relativedelta(months=1)
    next_month = next_month.strftime(strftime)
    return next_month


def email_parts(email_part):
    date_url = url_date()
    base_url = os.getenv("BASE_URL")
    todays_month = get_next_month("%B")
    catalogue_url = construct_catalogue_url(base_url, date_url)
    with open("email_parts.json", "r") as parts:
        parts = parts.read()
    json_email_parts = json.loads(parts)
    body = json_email_parts["parts"][email_part]["body"].format(
        link=catalogue_url, month=todays_month)
    sender = os.getenv("COMIC_BUTLER_EMAIL")
    title = json_email_parts["parts"][email_part]["subject"].format(
        month=todays_month)
    return body, sender, title


def url_date():
    next_month_date = get_next_month("%b%y")
    return next_month_date
