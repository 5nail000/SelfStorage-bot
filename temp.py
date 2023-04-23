import sqlite3

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
token = '5778281282:AAHAPOtzeP7_qofFxkkb0KxgSJzhMarWn-Y'
bot = telebot.TeleBot(token)


def print_order_text(order: dict):
    text = '\n\n'
    text += "Текущие данные заказа:\n"
    for key, value in order.items():
        if key == 'duration':
            text += f'Длительность аренды - {value}мес\n'
        if key == 'measure_later':
            text += "Вес и объём - уточним позднее\n"
        if key == 'delivery':
            text += 'Доставка - нужна' if value else 'Доставка - самостоятельно'

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

    current_order = {'is_new': True}
    if '#order#' in call.data:
       current_order = json.loads(call.data.split('#order#')[-1])
       current_order.update({'is_new': False})

    if call.data == "main_page":

        dialog_text = "Текст стартовой страницы"
        markup = InlineKeyboardMarkup()
        markup.row_width = 1
        button1 = InlineKeyboardButton('Арендовать место', callback_data='do_order')
        button2 = InlineKeyboardButton('Ознакомиться с подробностями', callback_data='show_info')
        button3 = InlineKeyboardButton('Мои Аренды', callback_data='show_orders')
        markup.add(button1, button2, button3)
        bot.edit_message_text(dialog_text, call.message.chat.id, call.message.id, reply_markup=markup)

    if "do_order" in call.data:

        dialog_text = "Вы определили какой вес и объём Вам необходимо сдать на хранение...\nИли Вам потребуется наша помощь?"
        markup = InlineKeyboardMarkup()
        markup.row_width = 1
        button1 = InlineKeyboardButton('Да, я знаю параметры', callback_data='order_diag1_yes')
        button2 = InlineKeyboardButton('Нет, мы определим позднее', callback_data='order_diag1_no')
        button3 = InlineKeyboardButton('<<-- Назад', callback_data='main_page')
        markup.add(button1, button2, button3)
        bot.edit_message_text(dialog_text, call.message.chat.id, call.message.id, reply_markup=markup)

    if call.data == "order_diag1_no":

        current_order.update({'measure_later': True})

        dialog_text = "На сколько месяцев Вам требуется аренда?"
        dialog_text += print_order_text(current_order)
        order_data = f'#order#{json.dumps(current_order)}'

        markup = InlineKeyboardMarkup()
        markup.row_width = 6
        button01 = InlineKeyboardButton('1', callback_data=f'order_months#01{order_data}')
        button02 = InlineKeyboardButton('2', callback_data=f'order_months#02{order_data}')
        button03 = InlineKeyboardButton('3', callback_data=f'order_months#03{order_data}')
        button04 = InlineKeyboardButton('4', callback_data=f'order_months#04{order_data}')
        button05 = InlineKeyboardButton('5', callback_data=f'order_months#05{order_data}')
        button06 = InlineKeyboardButton('6', callback_data=f'order_months#06{order_data}')
        button07 = InlineKeyboardButton('7', callback_data=f'order_months#07{order_data}')
        button08 = InlineKeyboardButton('8', callback_data=f'order_months#08{order_data}')
        button09 = InlineKeyboardButton('9', callback_data=f'order_months#09{order_data}')
        button10 = InlineKeyboardButton('10', callback_data=f'order_months#10{order_data}')
        button11 = InlineKeyboardButton('11', callback_data=f'order_months#11{order_data}')
        button12 = InlineKeyboardButton('12', callback_data=f'order_months#12{order_data}')
        markup.add(button01, button02, button03, button04, button05, button06,
                   button07, button08, button09, button10, button11, button12)
        bot.edit_message_text(dialog_text, call.message.chat.id, call.message.id, reply_markup=markup)

    if "order_months" in call.data:

        duration = call.data
        duration = int(duration.split("#")[1])
        if duration:
            current_order.update({'duration': duration})

        dialog_text = "Вам помочь с доставкой, или Вы доставите вещи самостоятельно?"
        dialog_text += print_order_text(current_order)
        order_data = f'#order#{json.dumps(current_order)}'

        markup = InlineKeyboardMarkup()
        markup.row_width = 1
        button1 = InlineKeyboardButton('Да, организуйте доставку сами', callback_data=f'order_delivery_yes')
        button2 = InlineKeyboardButton('Нет, я доставлю', callback_data=f'order_delivery_time')
        markup.add(button1, button2)
        bot.edit_message_text(dialog_text, call.message.chat.id, call.message.id, reply_markup=markup)

    if "order_delivery_yes" in call.data:

        current_order.update({'delivery': True})

        dialog_text = "Хорошо. Напишите в чат адрес, от куда надо будет забрать вещи."
        dialog_text += print_order_text(current_order)
        order_data = f'#order#{json.dumps(current_order)}'

        markup = InlineKeyboardMarkup()
        markup.row_width = 1
        button1 = InlineKeyboardButton('<<-- Назад', callback_data=f'order_months{order_data}')
        markup.add(button1)
        bot.edit_message_text(dialog_text, call.message.chat.id, call.message.id, reply_markup=markup)

    if "order_delivery_time" in call.data:

        order_data = f'#order#{json.dumps(current_order)}'

        dialog_text = "Определите время"
        dialog_text += "\n\n"
        dialog_text += "Текущие данные заказа:\n"
        dialog_text += "Вес и объём - уточним позднее\n"
        dialog_text += f"Длительность аренды - мес."

        markup = InlineKeyboardMarkup()
        markup.row_width = 1
        button1 = InlineKeyboardButton('<<-- Назад', callback_data=f'order_months{order_data}')
        markup.add(button1)
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
