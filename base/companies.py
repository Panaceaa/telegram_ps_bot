import pandas as pd
import psycopg2


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
exchanges = ['NasdaqGS', 'NasdaqGM', 'NasdaqCM', 'NYSE', 'TSX']


def company_industry():
    df = pd.read_excel('indname.xls', sheet_name='Global alphabetical')[
        ['Company Name', 'Exchange:Ticker', 'Industry Group']]
    df = df.dropna(axis=0)
    df.loc[:, 'ticker'] = df['Exchange:Ticker'].apply(lambda x: x.split(':')[1])
    df.loc[:, 'exchange'] = df['Exchange:Ticker'].apply(lambda x: x.split(':')[0])
    df = df[df['exchange'].isin(exchanges)]

    df = df[['Company Name', 'ticker', 'Industry Group']]
    rows = list(df.itertuples(index=False, name=None))
    cur.execute(f"DELETE FROM company_industry")
    cur.executemany(f"INSERT INTO company_industry (name, ticker, industry) VALUES (%s, %s, %s)", rows)
    conn.commit()


def industry_ps():
    url = 'https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/psdata.html'
    dg = pd.read_html(url, header=0)
    dg = dg[0].replace('  ', ' ')
    dg['Net Margin'] = ((dg['Net Margin'].str[:-1]).astype(float)/100).round(3)
    dg['Pre-tax  Operating Margin'] = ((dg['Pre-tax  Operating Margin'].str[:-1]).astype(float)/100).round(3)

    dg['Industry  Name'] = dg['Industry  Name'].replace('\s+', ' ', regex=True)
    dg = dg.iloc[:, [0, 2, 3, 4, 5]]

    url_2 = 'http://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/wcdata.html'
    dg_2 = pd.read_html(url_2, header=0)
    dg_2 = dg_2[0].replace('  ', ' ')
    dg_2['Acc  Rec/ Sales'] = (dg_2['Acc  Rec/ Sales'].str[:-1].astype(float) / 100).round(3)
    dg_2['Inventory/Sales'] = (dg_2['Inventory/Sales'].str[:-1].astype(float) / 100).round(3)
    dg_2['Acc  Pay/ Sales'] = (dg_2['Acc  Pay/ Sales'].str[:-1].astype(float) / 100).round(3)
    dg_2['Non-cash  WC/ Sales'] = (dg_2['Non-cash  WC/ Sales'].str[:-1].astype(float) / 100).round(3)

    dg_2['Industry Name'] = dg_2['Industry Name'].replace('\s+', ' ', regex=True)
    dg_2 = dg_2.iloc[:, [0, 2, 3, 4, 5]]

    dg = dg.rename(columns={'Industry  Name': 'Industry Name'})
    dg = dg.merge(dg_2, on='Industry Name')


    rows = list(dg.itertuples(index=False, name=None))

    cur.execute(f"DELETE FROM industry_ps")
    cur.executemany(f"INSERT INTO industry_ps (industry, price_to_sales, net_margin, ev_to_sales, pre_tax_opr_margin, acc_rec_to_sales, inventory_to_sales, acc_pay_to_sales, non_cash_wc_to_sales) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", rows)
    conn.commit()


industry_ps()
# company_industry()
