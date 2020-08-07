import argparse

import requests
from bs4 import BeautifulSoup as bs


def has_error(res):
    soup = bs(res.text, 'html.parser')
    return len(soup.find_all("div", {"class": 'msgErro'})) > 0 or res.status_code != 200


def parse_price(price):
    return 1 / float(price.replace(",", "."))


def parse_date(dt):
    if len(dt) != 8:
        return False
    return f"{dt[6:8]}/{dt[4:6]}/{dt[:4]}"


def is_valid_row(row):
    currency_classes = ['fundoPadraoBClaro2', 'fundoPadraoBClaro3']
    return row.has_attr('class') and row['class'][0] in currency_classes


def get_country_relation():
    res = requests.get(
        "https://ptax.bcb.gov.br/ptax_internet/consultarTabelaMoedas.do?method=consultaTabelaMoedas")
    soup = bs(res.text, 'html.parser')

    rows = [row for row in soup.find_all('tr') if is_valid_row(row)]

    relation = {}
    for row in rows:
        cells = row.find_all('td')
        currency = cells[2].text
        country = cells[4].text
        relation[currency] = country

    return relation


def currency_to_dict(row, relation):
    cells = row.find_all('td')
    symbol = cells[2].text

    return {
        "currency": symbol,
        "country": relation[symbol],
        "price": parse_price(cells[-1].text)
    }


def get_currencies(date):
    data = {
        'RadOpcao': 2,
        'DATAINI': date,
        'ChkMoeda': 61
    }

    res = requests.post(
        "https://ptax.bcb.gov.br/ptax_internet/consultaBoletim.do?method=consultarBoletim", data)

    if has_error(res):
        raise "Invalid Date Error"

    country_relation = get_country_relation()
    soup = bs(res.text, 'html.parser')
    rows = soup.find_all('tr')

    return [currency_to_dict(row, country_relation) for row in rows if is_valid_row(row)]


def get_lowest_currency(date):
    try:
        currencies = get_currencies(date)
    except:
        return 'x'
    lowest = sorted(currencies, key=lambda c: c['price'])[0]
    return f"Currency: {lowest['currency']} Country: {lowest['country']} Price: {lowest['price']:.10f} USD"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Fetch the lowest priced currency (in relation to USD)')
    parser.add_argument('date', metavar='date', type=str, nargs=1,
                        help='date to search for the currency - YYYYMMDD format')

    args = parser.parse_args()
    date = parse_date(args.date[0])
    if not date:
        print('Wrong date format')
    else:
        print(get_lowest_currency(date))
