import sqlite3

import datetime
from datetime import date
import sys
import logging
import time
import json
import signal
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from environs import Env



logging.basicConfig(filename='bot.log', level=logging.INFO)


env = Env()
env.read_env(override=True)
bot = telebot.TeleBot(env.str("5778281282:AAHAPOtzeP7_qofFxkkb0KxgSJzhMarWn-Y"))


def signal_handler(signum, frame):
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)

ADRESS = "Adress"

MEETUP_TEXT = "Приветствую в чат боте сервиса по аренде складкского помещения для вещей."

EXAMPLES_INTRO_TEXT = "Ниже перечислены основные примеры испоьзования:"

EXAMPLES_OS_USE = [
    "Вы можете положить свой старый хлам, который жалко выбрасывать.",
    "Вы можете складировать достаточно объёмные сезонные предметы: велосипед, снегоуборочную машину и т.д.",
]

RULES_INTRO_TEXT = "Для склада существует ряд правил:"

RULES = [
    "Не использовать склад в злоумышленных целях",
    "Не обманывать работников склада в целях скрытно положить на хранение запрещённый предмет",
]

UNALLOWED_ITEMS = [
    "Жидкости",
    "Органические продукты",
    "Животных",
    "Химические реагенты",
    "Облучённые чрезмерной дозой радиации предметы",
    "Все прочие запрещённые для хранения предметы по УК РФ",
]

ALLOWED_ITEMS = [
    "Книги",
    "Бытовую технику",
    "Спортивный инвентарь",
    "Одежду",
    "Предметы роскоши",
]


def get_intro_message_text() -> str:
    return MEETUP_TEXT + "\n" + EXAMPLES_INTRO_TEXT + "\n" + "\n".join(EXAMPLES_OS_USE)


def get_rules_messages_texts() -> tuple[str, str, str]:
    main_rules = RULES_INTRO_TEXT + "\n" + "\n".join(RULES)
    allowed_items = "Разрешено сдавать на хранение:" + "\n" + "\n".join(ALLOWED_ITEMS)
    unallowed_items = "Запрещено сдавать на хранение:" + "\n" + "\n".join(UNALLOWED_ITEMS)
    return main_rules, allowed_items, unallowed_items


def print_order_text(order: dict):

    text = '\n\n'
    text += "Данные заказа:\n"
    if order:
        for key, value in order.items():
            if key == 'phone_number':
                text += f'Номер телефона: {value}\n'
            if key == 'duration':
                text += f'Длительность аренды - {value}мес\n'
            if key == 'size':
                text += f"Объём: {value} м^3 \n" if value else "Объём не указан\n"
            if key == 'weight':
                text += f"Вес: {value} кг\n" if value else "Вес не указан\n"
            if key == 'delivery':
                text += 'Доставка - нужна\n' if value else 'Доставка - самостоятельно\n'
            if key == 'adress':
                text += f'Адресс: {value}\n' if value else 'Адресс не указан\n'
            if key == 'begining_day':
                text += f"Дата начала аренды: {value}\n"
            if key == 'delivery_hour':
                text += f"Время для доставки: {value}:00\n"

    return text


@bot.message_handler(commands=['start'])
def send_welcome(message):
    start_text = "Привет! Прежде чем оформить заказ, давайте Вы разрешите нам пользоваться данными которые нам необходимо будет получить от Вас? \n \n Вот ссылка на текст соглашения, нажимая на кнопку продолжить - вы подтверждаете что ознакомились с нашими условиями и приняли их."
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(InlineKeyboardButton("ПРИНИМАЮ >>", callback_data="main_page"))
    bot.send_message(message.chat.id, start_text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):

    current_order = bot.__dict__['user_order'] if 'user_order' in bot.__dict__.keys() else None

    connection = sqlite3.connect("./selfstorage.db")
    cursor = connection.cursor()
    user_str = cursor.execute(f"SELECT * FROM users WHERE user_id={call.from_user.id}").fetchall()
    if not user_str:
        insert_script = "INSERT INTO users (user_id,tg_id,name,phone) "\
                        f"VALUES(\'{call.from_user.id}\',\'{call.from_user.id}\','','');"
        print(insert_script)
        cursor.execute(insert_script)
        connection.commit()

    if call.data == "main_page":

        if current_order and 'delivery_hour' in current_order.keys() and current_order["delivery_hour"]:
            dialog_text = "Ваш заказ принят. Скоро, с Вами свяжутся наши менеджеры"
            dialog_text += print_order_text(current_order)
            bot.send_message(call.message.chat.id, dialog_text)
            connection = sqlite3.connect("./selfstorage.db")
            cursor = connection.cursor()
            orders_num = cursor.execute("SELECT MAX(order_id) FROM orders").fetchall()[0][0]
            year = int(current_order['begining_day'].split(".")[-1])
            month = int(current_order['begining_day'].split(".")[1]) + current_order['duration']
            if month > 12:
                month %= 12
                year += 1
            day = int(current_order['begining_day'].split(".")[0])
            execution_script = "INSERT INTO orders (order_id,user_id,weight,capacity,start_date,end_date,cost,delivery,delivery_time,address,revisited) "\
                f"VALUES(\'{int(orders_num)+1 if orders_num else 0}\',\'{call.from_user.id}\',\'{current_order['weight']}\',\'{current_order['size']}\',\'{current_order['begining_day']}\',\'{str(day) + '.' + str(month) + '.' + str(year)}\',\'{int(current_order['weight']*current_order['size']/10)}\',\'{str(current_order['delivery']).lower()}\',\'{current_order['delivery_hour']}\',\'{current_order['adress']}\',\'false\');"
            cursor.executescript(execution_script)
            connection.commit()
            bot.__dict__.pop('user_order')

        dialog_text = "Текст стартовой страницы"
        markup = InlineKeyboardMarkup()
        markup.row_width = 1
        button1 = InlineKeyboardButton('Арендовать место', callback_data='phone_number')
        button2 = InlineKeyboardButton('Правила', callback_data='show_info')
        button3 = InlineKeyboardButton('Мои Аренды', callback_data='show_orders')
        button4 = InlineKeyboardButton('Мои Предметы', callback_data='show_items')
        button5 = InlineKeyboardButton('Забрать предмет', callback_data='chose_item')
        markup.add(button1, button3, button4, button5, button2)
        bot.edit_message_text(dialog_text, call.message.chat.id, call.message.id, reply_markup=markup)

    if "phone_number" in call.data:

        current_order = {'size': 0, 'weight': 0}
        bot.__dict__['user_order'] = current_order

        def get_phone_number(message):
            current_order.update({'phone_number': message.text})
            bot.__dict__['user_order'] = current_order

        dialog_text = "Хорошо. Напишите в чат номер телефона."
        dialog_text += print_order_text(current_order)

        markup = InlineKeyboardMarkup()
        markup.row_width = 1
        button_1 = InlineKeyboardButton('Подтвердить номер телефона', callback_data='new_order')
        button_pre = InlineKeyboardButton('<< Назад', callback_data='main_page')
        markup.add(button_1, button_pre)
        bot.edit_message_text(dialog_text, call.message.chat.id, call.message.id, reply_markup=markup)
        bot.register_next_step_handler(call.message, get_phone_number)

    if "new_order" in call.data:

        dialog_text = "Вы определили какой вес и объём Вам необходимо сдать на хранение...\nИли Вам потребуется наша помощь?"
        markup = InlineKeyboardMarkup()
        markup.row_width = 1
        button1 = InlineKeyboardButton('Да, я знаю параметры', callback_data='order_diag1_yes')
        button2 = InlineKeyboardButton('Нет, мы определим позднее', callback_data='order_duration')
        button3 = InlineKeyboardButton('<< Назад', callback_data='phone_number')
        markup.add(button1, button2, button3)
        bot.edit_message_text(dialog_text, call.message.chat.id, call.message.id, reply_markup=markup)

    if call.data == "order_diag1_yes":

        def get_size(message):
            try:
                current_order.update({'size': float(message.text)})
                bot.__dict__['user_order'] = current_order
            except ValueError:
                bot.send_message(
                    message.chat.id,
                    "Не могу понять число, повторите ввод как в примере: '32.4324'",
                )

        dialog_text = "Хорошо. Напишите в чат объём в кубических метрах (пример: '34.2313')."
        dialog_text += print_order_text(current_order)

        markup = InlineKeyboardMarkup()
        markup.row_width = 1
        button_1 = InlineKeyboardButton('Подтвердить объём', callback_data='order_diag1_yes_2')
        button_pre = InlineKeyboardButton('<< Назад', callback_data='new_order')
        markup.add(button_1, button_pre)
        bot.edit_message_text(dialog_text, call.message.chat.id, call.message.id, reply_markup=markup)
        bot.register_next_step_handler(call.message, get_size)

    if call.data == "order_diag1_yes_2":

        def get_weight(message):
            try:
                current_order.update({'weight': float(message.text)})
                bot.__dict__['user_order'] = current_order
            except ValueError:
                bot.send_message(
                    message.chat.id,
                    "Не могу понять число, повторите ввод как в примере: '32.4324'",
                )

        dialog_text = "Хорошо. Напишите в чат вес в килограммах (пример: '34.2313')."
        dialog_text += print_order_text(current_order)

        markup = InlineKeyboardMarkup()
        markup.row_width = 1
        button_1 = InlineKeyboardButton('Подтвердить вес', callback_data='order_duration')
        button_pre = InlineKeyboardButton('<< Назад', callback_data='order_diag1_yes')
        markup.add(button_1, button_pre)
        bot.edit_message_text(dialog_text, call.message.chat.id, call.message.id, reply_markup=markup)
        bot.register_next_step_handler(call.message, get_weight)

    if call.data == "order_duration":

        dialog_text = "На сколько месяцев Вам требуется аренда?"
        dialog_text += print_order_text(current_order)

        markup = InlineKeyboardMarkup()
        markup.row_width = 6
        button01 = InlineKeyboardButton('1', callback_data='order_delivery_needs#01')
        button02 = InlineKeyboardButton('2', callback_data='order_delivery_needs#02')
        button03 = InlineKeyboardButton('3', callback_data='order_delivery_needs#03')
        button04 = InlineKeyboardButton('4', callback_data='order_delivery_needs#04')
        button05 = InlineKeyboardButton('5', callback_data='order_delivery_needs#05')
        button06 = InlineKeyboardButton('6', callback_data='order_delivery_needs#06')
        button07 = InlineKeyboardButton('7', callback_data='order_delivery_needs#07')
        button08 = InlineKeyboardButton('8', callback_data='order_delivery_needs#08')
        button09 = InlineKeyboardButton('9', callback_data='order_delivery_needs#09')
        button10 = InlineKeyboardButton('10', callback_data='order_delivery_needs#10')
        button11 = InlineKeyboardButton('11', callback_data='order_delivery_needs#11')
        button12 = InlineKeyboardButton('12', callback_data='order_delivery_needs#12')
        button_pre = InlineKeyboardButton('<< Назад', callback_data="new_order")

        markup.row(button01, button02, button03, button04, button05, button06)
        markup.row(button07, button08, button09, button10, button11, button12)
        markup.row(button_pre)
        bot.edit_message_text(dialog_text, call.message.chat.id, call.message.id, reply_markup=markup)

    if "order_delivery_needs" in call.data:

        duration = call.data
        if duration.split("#")[-1]:
            duration_months = int(duration.split("#")[-1])
            current_order.update({'duration': duration_months})
            bot.__dict__['user_order'] = current_order

        dialog_text = "Вам помочь с доставкой, или Вы доставите вещи самостоятельно?"
        dialog_text += print_order_text(current_order)

        markup = InlineKeyboardMarkup()
        markup.row_width = 1
        button1 = InlineKeyboardButton('Да, организуйте доставку сами', callback_data='order_delivery_address')
        button2 = InlineKeyboardButton(f'Нет, я доставлю (адресс: {ADRESS})', callback_data='order_begining_month')
        button_pre = InlineKeyboardButton('<< Назад', callback_data="order_duration")
        markup.add(button1, button2, button_pre)
        bot.edit_message_text(dialog_text, call.message.chat.id, call.message.id, reply_markup=markup)

    if "order_delivery_address" in call.data:

        def get_adress(message):
            current_order.update({'delivery': True})
            bot.__dict__['user_order'] = current_order
            current_order.update({'adress': message.text})
            bot.__dict__['user_order'] = current_order

        current_order.update({'delivery': True})
        bot.__dict__['user_order'] = current_order

        dialog_text = "Хорошо. Напишите в чат адрес, от куда надо будет забрать вещи."
        dialog_text += print_order_text(current_order)

        markup = InlineKeyboardMarkup()
        markup.row_width = 1
        button_1 = InlineKeyboardButton('Подтвердить адрес', callback_data='order_begining_month#')
        button_pre = InlineKeyboardButton('<< Назад', callback_data='order_delivery_needs#')
        markup.add(button_1, button_pre)
        bot.edit_message_text(dialog_text, call.message.chat.id, call.message.id, reply_markup=markup)
        bot.register_next_step_handler(call.message, get_adress)
        
    if "order_begining_month" in call.data:

        if 'delivery' not in current_order.keys():
            current_order.update({'delivery': False})
            bot.__dict__['user_order'] = current_order
            current_order.update({'adress': ADRESS})
            bot.__dict__['user_order'] = current_order

        dialog_text = "Определите месяц(начала аренды)"
        dialog_text += print_order_text(current_order)

        markup = InlineKeyboardMarkup()
        button01 = InlineKeyboardButton('Январь', callback_data='order_begining_day#1')
        button02 = InlineKeyboardButton('Февраль', callback_data='order_begining_day#2')
        button03 = InlineKeyboardButton('Март', callback_data='order_begining_day#3')
        button04 = InlineKeyboardButton('Апрель', callback_data='order_begining_day#4')
        button05 = InlineKeyboardButton('Май', callback_data='order_begining_day#5')
        button06 = InlineKeyboardButton('Июнь', callback_data='order_begining_day#6')
        button07 = InlineKeyboardButton('Июль', callback_data='order_begining_day#7')
        button08 = InlineKeyboardButton('Август', callback_data='order_begining_day#8')
        button09 = InlineKeyboardButton('Сентябрь', callback_data='order_begining_day#9')
        button10 = InlineKeyboardButton('Октябрь', callback_data='order_begining_day#10')
        button11 = InlineKeyboardButton('Ноябрь', callback_data='order_begining_day#11')
        button12 = InlineKeyboardButton('Декабрь', callback_data='order_begining_day#12')

        markup.row(button01, button02, button03, button04)
        markup.row(button05, button06, button07, button08)
        markup.row(button09, button10, button11, button12)
        if current_order["delivery"]:
            markup.row(InlineKeyboardButton('<< Назад', callback_data='order_delivery_address'))
        else:
            markup.row(InlineKeyboardButton('<< Назад', callback_data='order_delivery_needs#'))

        bot.edit_message_text(dialog_text, call.message.chat.id, call.message.id, reply_markup=markup)

    if "order_begining_day" in call.data:

        begining_month = call.data
        if begining_month.split("#")[-1]:
            begining_month = int(begining_month.split("#")[-1])
            current_order.update({'begining_month': begining_month})
            bot.__dict__['user_order'] = current_order

        month = current_order['begining_month']
        current_year = datetime.datetime.now().year
        days_in_month = (datetime.date(current_year, month+1, 1)-datetime.date(current_year, month, 1)).days if month < 12 else 31
        buttons = []
        for day in range(days_in_month):
            buttons.append(InlineKeyboardButton(day+1, callback_data=f'order_delivery_time#{day+1}'))

        dialog_text = "Определите день(начала аренды)"
        dialog_text += print_order_text(current_order)

        markup = InlineKeyboardMarkup()
        markup.row(*buttons)
        markup.row(InlineKeyboardButton('<< Назад', callback_data='order_begining_month'))
        bot.edit_message_text(dialog_text, call.message.chat.id, call.message.id, reply_markup=markup)

    if "order_delivery_time" in call.data:

        begining_day = call.data
        if begining_day.split("#")[-1]:
            begining_day = int(begining_day.split("#")[-1])
            year = datetime.datetime.now().year
            today_date = datetime.date(datetime.datetime.now().year,
                         datetime.datetime.now().month,
                         datetime.datetime.now().day)
            date_delta = (datetime.date(year, current_order['begining_month'], begining_day) - today_date).days
            if date_delta < 1:
                year += 1

            current_order.update({'begining_day': f'{begining_day}.{current_order["begining_month"]}.{year}'})
            bot.__dict__['user_order'] = current_order

        if current_order['delivery']:
            dialog_text = "Выберите удобное Вам время, во сколько доставке забрать Ваши вещи"
        else:
            dialog_text = "Выберите ориентировочное время, во сколько Вы приедете к нам в день начала аренды"

        dialog_text += print_order_text(current_order)

        buttons = []
        for hour in range(8, 22):
            buttons.append(InlineKeyboardButton(f'{hour+1}:00', callback_data=f'order_resume#{hour+1}'))

        markup = InlineKeyboardMarkup()
        markup.row(*buttons)
        markup.row(InlineKeyboardButton('<< Назад', callback_data='order_begining_day#'))
        bot.edit_message_text(dialog_text, call.message.chat.id, call.message.id, reply_markup=markup)

    if "order_resume" in call.data:
        delivery_hour = call.data
        if delivery_hour.split("#")[-1]:
            delivery_hour = int(delivery_hour.split("#")[-1])
            current_order.update({'delivery_hour': delivery_hour})
            bot.__dict__['user_order'] = current_order

        dialog_text = f"Подтвердите данные оставленные в заявке.\n(наши менеджеры свяжутся с Вами сразу как данные будут обработанны).\n"
        if "size" in current_order.keys() and "weight" in current_order.keys():
            price = current_order["size"]*current_order["weight"]/10
            dialog_text += f"Цена содержания в месяц = {price}"
        dialog_text += print_order_text(current_order)

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton('Да, всё верно', callback_data='main_page'))
        markup.add(InlineKeyboardButton('<< Назад', callback_data='order_delivery_time#'))
        bot.edit_message_text(dialog_text, call.message.chat.id, call.message.id, reply_markup=markup)

    if "order_accepting" in call.data:

        dialog_text = "Ваш заказ принят. Скоро, с Вами свяжутся наши менеджеры"
        dialog_text += print_order_text(current_order)

        bot.send_message(call.message.chat.id, dialog_text)
        bot.edit_message_text(dialog_text, call.message.chat.id, call.message.id, reply_markup=markup)

    if "show_info" in call.data:

        dialog_text = "\n\n".join(get_rules_messages_texts())
        markup = InlineKeyboardMarkup()
        markup.row_width = 1
        markup.add(InlineKeyboardButton('<< Назад', callback_data='main_page'))
        bot.edit_message_text(dialog_text, call.message.chat.id, call.message.id, reply_markup=markup)

    if "show_items" in call.data:
        
        items_ids = []

        connection = sqlite3.connect("./selfstorage.db")
        cursor = connection.cursor()
        items_ids = [str(item[0]) + " - " + str("в хранилище" if item[1]=="false" else "выводится/выведен из хранилища") for item in cursor.execute(f"SELECT order_id, revisited FROM orders WHERE user_id={call.from_user.id}").fetchall()]

        dialog_text = "Предметы:\n" + "\n".join(items_ids)
        markup = InlineKeyboardMarkup()
        markup.row_width = 1
        markup.add(InlineKeyboardButton('<< Назад', callback_data='main_page'))
        bot.edit_message_text(dialog_text, call.message.chat.id, call.message.id, reply_markup=markup)

    if "chose_item" in call.data:

        def get_id(message):
            try:
                current_order.update({'id': int(message.text)})
                bot.__dict__['user_order'] = current_order

                connection = sqlite3.connect("./selfstorage.db")
                cursor = connection.cursor()
                update_script = f"UPDATE orders SET revisited=\'true\' WHERE user_id=\'{call.from_user.id}\' AND order_id=\'{current_order['id']}\'"
                cursor.execute(update_script)
                connection.commit()

                bot.send_message(
                    call.message.chat.id,
                    f"Ваш QR код: {hash(str(call.from_user.id))}",
                )
            except ValueError:
                bot.send_message(
                    message.chat.id,
                    "Не могу понять число, повторите ввод как в примере: '32'",
                )

        current_order = {}
        bot.__dict__['user_order'] = current_order
        
        items_ids = []

        connection = sqlite3.connect("./selfstorage.db")
        cursor = connection.cursor()
        items_ids = [str(item[0]) + " - " + str("в хранилище" if item[1]=="false" else "выводится/выведена из хранилища") for item in cursor.execute(f"SELECT order_id, revisited FROM orders WHERE user_id={call.from_user.id} AND revisited=\'false\'").fetchall()]

        dialog_text = "Введите в чат номер предмета для удаления:\nНомера предметов в ваших хранилищах:\n\n" + "\n".join(items_ids)
        markup = InlineKeyboardMarkup()
        markup.row_width = 1
        markup.add(InlineKeyboardButton('Подтвердить ID предмета', callback_data='main_page'))
        markup.add(InlineKeyboardButton('<< Назад', callback_data='main_page'))
        bot.edit_message_text(dialog_text, call.message.chat.id, call.message.id, reply_markup=markup)
        bot.register_next_step_handler(call.message, get_id)


def main():
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as error:
            print(error)
            time.sleep(5)


if __name__ == '__main__':
    main()
