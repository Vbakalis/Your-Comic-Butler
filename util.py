from datetime import date
from dateutil import relativedelta

async def construct_catalogue_url(base_url, date_url):
    return f"{base_url}Catalog?batch={date_url}"


async def get_next_month(strftime):
    today = date.today()
    next_month = today + relativedelta.relativedelta(months=1)
    next_month = next_month.strftime(strftime)
    return next_month
