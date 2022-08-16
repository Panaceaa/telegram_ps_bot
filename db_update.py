import psycopg2

PROD_DATABASE_URI = "host=35.228.5.243 dbname='postgres' user='postgres' password='f4wlB3iOhha1HgF1'"
conn = psycopg2.connect(PROD_DATABASE_URI)
cur = conn.cursor()


def response_data(row):
    cur.execute(
        """INSERT INTO taxforme.telegram_response (chat_id, ticker, start_date, response_date_unix, product) 
           VALUES (%s, %s, %s, %s, %s);""", row)
    conn.commit()


def user_data(row):
    try:
        cur.execute("""SELECT * FROM taxforme.telegram_users""", row)
    except Exception:
        conn.rollback()
    data = cur.fetchall()
    if not data:
        pass
    else:
        users = [x[2] for x in data]
        product = [x[3] for x in data]
        if row[2] in users and row[3] in product:
            return
        cur.execute("""INSERT INTO taxforme.telegram_users (username, user_nick, chat_id, product) 
                       VALUES (%s, %s, %s, %s);""", row)
        conn.commit()


def user_error(chat_id, ticker, request_time, product):
    try:
        cur.execute(f"""INSERT INTO taxforme.telegram_error_request (chat_id, ticker, request_time, product) VALUES (%s, %s, %s, %s)""",
                    (chat_id, ticker, request_time, product))
        conn.commit()
    except:
        conn.rollback()