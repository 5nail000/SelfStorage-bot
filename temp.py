import sqlite3

import datetime
import logging
import time
import json
import signal
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from environs import Env
from datetime import date


logging.basicConfig(filename='bot.log', level=logging.INFO)


env = Env()
env.read_env(override=True)
token = '5778281282:AAHAPOtzeP7_qofFxkkb0KxgSJzhMarWn-Y'
bot = telebot.TeleBot(token)


def print_order_text(order: dict):

    text = '\n\n'
    text += "Данные заказа:\n"
    if order:
        for key, value in order.items():
            if key == 'duration':
                text += f'Длительность аренды - {value}мес\n'
            if key == 'measure_later':
                text += "Вес и объём - уточним позднее\n"
            if key == 'delivery':
                text += 'Доставка - нужна\n' if value else 'Доставка - самостоятельно\n'
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

    if call.data == "main_page":

        if current_order:
            dialog_text = "Ваш заказ принят. Скоро, с Вами свяжутся наши менеджеры"
            dialog_text += print_order_text(current_order)
            bot.send_message(call.message.chat.id, dialog_text)
            bot.__dict__.pop('user_order')

        dialog_text = "Текст стартовой страницы"
        markup = InlineKeyboardMarkup()
        markup.row_width = 1
        button1 = InlineKeyboardButton('Арендовать место', callback_data='new_order')
        button2 = InlineKeyboardButton('Ознакомиться с подробностями', callback_data='show_info')
        button3 = InlineKeyboardButton('Мои Аренды', callback_data='show_orders')
        markup.add(button1, button2, button3)
        bot.edit_message_text(dialog_text, call.message.chat.id, call.message.id, reply_markup=markup)

    if "new_order" in call.data:

        dialog_text = "Вы определили какой вес и объём Вам необходимо сдать на хранение...\nИли Вам потребуется наша помощь?"
        markup = InlineKeyboardMarkup()
        markup.row_width = 1
        button1 = InlineKeyboardButton('Да, я знаю параметры', callback_data='order_diag1_yes')
        button2 = InlineKeyboardButton('Нет, мы определим позднее', callback_data='order_duration')
        button3 = InlineKeyboardButton('<< Назад', callback_data='main_page')
        markup.add(button1, button2, button3)
        bot.edit_message_text(dialog_text, call.message.chat.id, call.message.id, reply_markup=markup)

    if call.data == "order_duration":

        current_order = {'measure_later': True}
        bot.__dict__['user_order'] = current_order

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
        button2 = InlineKeyboardButton('Нет, я доставлю', callback_data='order_begining_month')
        button_pre = InlineKeyboardButton('<< Назад', callback_data="order_duration")
        markup.add(button1, button2, button_pre)
        bot.edit_message_text(dialog_text, call.message.chat.id, call.message.id, reply_markup=markup)

    if "order_delivery_address" in call.data:

        current_order.update({'delivery': True})
        bot.__dict__['user_order'] = current_order

        dialog_text = "Хорошо. Напишите в чат адрес, от куда надо будет забрать вещи."
        dialog_text += print_order_text(current_order)

        markup = InlineKeyboardMarkup()
        markup.row_width = 1
        button_pre = InlineKeyboardButton('<< Назад', callback_data='order_delivery_needs#')
        markup.add(button_pre)
        bot.edit_message_text(dialog_text, call.message.chat.id, call.message.id, reply_markup=markup)

    if "order_begining_month" in call.data:

        if 'delivery' not in current_order.values():
            current_order.update({'delivery': False})
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

        dialog_text = "Подтвердите данные оставленные в заявке.\n(наши менеджеры свяжутся с Вами сразу как данные будут обработанны)"
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


def main():
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as error:
            print(error)
            time.sleep(5)


if __name__ == '__main__':
    main()
