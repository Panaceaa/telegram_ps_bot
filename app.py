# coding=utf-8
# coding=utf-8
import datetime
import io
from telegram.ext import Updater, filters
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, ConversationHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import ParseMode
import re
import calc_ps
import db_update
import time


token = '2126898244:AAHAukk7Xh5-Z2HAwSob2jrTvd8iw5EezeQ'
updater = Updater(token, use_context=True)

START = 'Привет!😊 Введи тикер акции о которой хочешь узнать больше.'
product = 'ps_growth'


def start(update, context):
    chat_id = update.message.chat.id
    updater.bot.send_message(chat_id=chat_id, text=START)
    db_update.user_data((update.message.chat.username, update.message.chat.first_name, int(update.message.chat.id), product))


def user_answer(update, context):
    chat_id = update.message.chat.id
    updater.bot.send_message(chat_id=chat_id, text='Уже ищу 🧐')
    symbol = update.message.text
    pattern = '[a-zA-z]'
    symbol = ''.join(x for x in re.findall(pattern, symbol)).upper()

    industry = calc_ps.select_database(symbol)
    ps = calc_ps.fmp_connection(symbol)
    pr = calc_ps.fmp_price(symbol)

    if industry is None:
        updater.bot.send_message(chat_id=chat_id, text=
                            "Тикер не найден 😿\n(Мы постараемся добавить компанию, если она существует)\n\n"
                            "Попробуй ввести другой.")
        db_update.user_error(chat_id, symbol, update.message.date, product)

    elif ps is None or pr is None:
        updater.bot.send_message(chat_id=chat_id, text=
                            "Выручка не найдена 😿\n(Мы скоро это проверим)\n\nПопробуй ввести другой тикер.")
        db_update.user_error(chat_id, symbol, update.message.date, product)

    else:
        ps_forward = calc_ps.ps_industry(industry['industry'].values[0])
        rev_gr = calc_ps.fmp_revenue(symbol)
        if rev_gr is None:
            rev_gr = 'Нет данных'
        name = industry['name'].values[0].rsplit('(')[0]
        m, gr = calc_ps.matrix(pr, ps, ps_forward, symbol)
        updater.bot.send_message(chat_id=chat_id, text=
                            f"<b>{name}</b>\n\n<b>Цена:</b> {round(pr, 1)} $\n\n<b>Рост выручки сейчас:</b> {rev_gr} в год\n\n📊Таблица показывает какой необходим рост выручки в год чтобы оправдать текущую цену акции, либо когда акция падает/растет на 10 %\n\n<b>Как понять таблицу:</b> выручка компании {name} должна ежегодно расти на {gr} в течение 5 лет чтобы оправдать текущую цену.\n<em>(Отрицательное значение показывает, что компания недооценена, либо инвесторы ожидают падения выручки)</em>",
                            parse_mode=ParseMode.HTML)
        updater.bot.send_message(chat_id=chat_id, text=m, parse_mode=ParseMode.HTML)

        db_update.response_data((chat_id, symbol, None, time.mktime(update.message.date.timetuple()), product))


updater.dispatcher.add_handler(CommandHandler('start', start))
updater.dispatcher.add_handler(MessageHandler(filters.Filters.text & (~ filters.Filters.command), callback=user_answer))
updater.start_polling()
