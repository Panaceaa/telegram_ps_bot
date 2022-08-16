import pandas as pd
import psycopg2
import requests
import time
import json
import numpy as np

api = '5999b507aa89f166a3682af1b59cf185'


def conn_barbacane():
    conn_config = {
        "dbname": "postgres",
        "user": "postgres",
        "host": "35.228.5.243",
        "password": "f4wlB3iOhha1HgF1",
        "schema": "taxforme"
    }

    schema = conn_config['schema']
    conn = psycopg2.connect(
        dbname=conn_config['dbname'],
        user=conn_config['user'],
        host=conn_config['host'],
        password=conn_config['password'],
        options=f'-c search_path={schema}',
    )
    return conn


conn = conn_barbacane()
cur = conn.cursor()


def select_database(ticker):
    query = f"SELECT * FROM company_industry WHERE ticker = '{ticker}'"
    cur.execute(query)
    resp = pd.DataFrame(cur.fetchall(), columns=['name', 'exchange_ticker', 'industry'])

    if resp.empty:
        return None
    else:
        return resp


def fmp_connection(ticker):
    url = f'https://financialmodelingprep.com/api/v3/ratios-ttm/{ticker}?apikey={api}'

    ps = ''
    k = 0
    while k < 10:
        try:
            resp = requests.get(url).text
            ps = json.loads(resp)[0]['priceToSalesRatioTTM']
            break
        except Exception:
            time.sleep(0.1)
            k += 1

    if k == 10:
        return None
    else:
        return ps


def fmp_price(ticker):
    url = f'https://financialmodelingprep.com/api/v3/quote-short/{ticker}?apikey={api}'

    pr = ''
    k = 0

    while k < 10:
        try:
            resp = requests.get(url).text
            pr = json.loads(resp)[0]['price']
            break
        except Exception:
            time.sleep(0.1)
            k += 1

    if k == 10:
        return None
    else:
        return pr


def fmp_revenue(ticker):
    url = f'https://financialmodelingprep.com/api/v3/income-statement/{ticker}?apikey={api}&limit=4'

    ps = ''
    k = 0
    while k < 10:
        try:
            resp = requests.get(url).text
            ps = [x['revenue'] for x in json.loads(resp)]
            break
        except Exception:
            time.sleep(0.1)
            k += 1

    if k == 10:
        return None

    if len(ps) < 4:
        return None

    return str(round(np.mean([ps[0]/ps[1] - 1, ps[1]/ps[2] - 1, ps[2]/ps[3] - 1])*100, 1)) + ' %'


def ps_industry(industry):
    query = f"SELECT * FROM industry_ps WHERE industry = '{industry}'"
    cur.execute(query)
    return cur.fetchall()[0][1]


def calc_growth(ps_forward, ps, n):
    return str(round(((ps/ps_forward) ** (1/n) - 1) * 100, 1)) + '%'


def create_result(pr, ps, ps_forward):
    term = [3, 5, 10]
    growth_ps = 0.1
    growth_pr = 0.1
    pts = [ps - ps*growth_ps, ps, ps + ps*growth_ps]
    prt = [pr - pr*growth_pr, pr, pr + pr*growth_pr]

    res = []
    for p in pts:
        for t in term:
            res.append(calc_growth(ps_forward, p, t))
    for t in term[::-1]:
        insert_at = 0
        if t == 3:
            res[insert_at:insert_at] = [str(t) + 'года']
        else:
            res[insert_at:insert_at] = [str(t) + 'лет ']
    for i, p in enumerate(prt):
        insert_at = 3 + 4 * i
        res[insert_at:insert_at] = [str(round(p, 1))]
    return res


def matrix(pr, ps, ps_forward, symbol):
    matrix_labels = create_result(pr, ps, ps_forward)
    insert_at = 0
    matrix_labels[insert_at:insert_at] = [symbol]
    space_header_1 = max([len(x) for x in [matrix_labels[1], matrix_labels[2], matrix_labels[3], matrix_labels[13]]])
    space_header_2 = max([len(x) for x in matrix_labels[::4]])
    string_table = f"""<pre>
    {matrix_labels[0]}{''.join(' ' for x in range(len(matrix_labels[0]), space_header_2))}┆{matrix_labels[1]}{''.join(' ' for x in range(len(matrix_labels[1]), space_header_1))} {matrix_labels[2]}{''.join(' ' for x in range(len(matrix_labels[2]), space_header_1))} {matrix_labels[3]}{''.join(' ' for x in range(len(matrix_labels[3]), space_header_1))}
    {''.join('-' for x in range(0, space_header_2))}┆{''.join('-' for x in range(0, sum([len(x) for x in matrix_labels[1:4]]) + 2))}
    {matrix_labels[4]}{''.join(' ' for x in range(len(matrix_labels[4]), space_header_2))}┆{matrix_labels[5]}{''.join(' ' for x in range(len(matrix_labels[5]), space_header_1))} {matrix_labels[6]}{''.join(' ' for x in range(len(matrix_labels[6]), space_header_1))} {matrix_labels[7]}{''.join(' ' for x in range(len(matrix_labels[7]), space_header_1))}
    {matrix_labels[8]}{''.join(' ' for x in range(len(matrix_labels[8]), space_header_2))}┆{matrix_labels[9]}{''.join(' ' for x in range(len(matrix_labels[9]), space_header_1))} {matrix_labels[10]}{''.join(' ' for x in range(len(matrix_labels[10]), space_header_1))} {matrix_labels[11]}{''.join(' ' for x in range(len(matrix_labels[11]), space_header_1))}
    {matrix_labels[12]}{''.join(' ' for x in range(len(matrix_labels[12]), space_header_2))}┆{matrix_labels[13]}{''.join(' ' for x in range(len(matrix_labels[13]), space_header_1))} {matrix_labels[14]}{''.join(' ' for x in range(len(matrix_labels[14]), space_header_1))} {matrix_labels[15]}{''.join(' ' for x in range(len(matrix_labels[15]), space_header_1))}
    </pre>"""
    return string_table, matrix_labels[10]


# data = select_database(ticker)
# data.loc[:, 'ticker'] = data['exchange_ticker'].apply(lambda x: x.split(':')[1])
