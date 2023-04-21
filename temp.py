import sqlite3

import sys
import logging
import time
import pprint
import signal
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from environs import Env


logging.basicConfig(filename='bot.log', level=logging.INFO)


env = Env()
env.read_env(override=True)
token = '5778281282:AAHAPOtzeP7_qofFxkkb0KxgSJzhMarWn-Y'
bot = telebot.TeleBot(token)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    start_text = "Привет! Прежде чем оформить заказ, давайте Вы разрешите нам пользоваться данными которые нам необходимо будет получить от Вас? \n \n Вот ссылка на текст соглашения, нажимая на кнопку продолжить - вы подтверждаете что ознакомились с нашими условиями и приняли их."
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(InlineKeyboardButton("ПРИНИМАЮ >>", callback_data="main_page"))
    bot.send_message(message.chat.id, start_text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):

    if call.data == "main_page":

        dialog_text = "Текст стартовой страницы"
        markup = InlineKeyboardMarkup()
        markup.row_width = 1
        button1 = InlineKeyboardButton('Арендовать место', callback_data='do_order')
        button2 = InlineKeyboardButton('Ознакомиться с подробностями', callback_data='show_info')
        button3 = InlineKeyboardButton('Мои Аренды', callback_data='show_orders')
        markup.add(button1, button2, button3)
        bot.edit_message_text(dialog_text, call.message.chat.id, call.message.id, reply_markup=markup)

    if call.data == "do_order":

        dialog_text = "Вы определили какой вес и объём Вам необходимо сдать на хранение...\nИли Вам потребуется наша помощь?"
        markup = InlineKeyboardMarkup()
        markup.row_width = 1
        button1 = InlineKeyboardButton('Да, я знаю параметры', callback_data='order_diag1_yes')
        button2 = InlineKeyboardButton('Нет, мы определим позднее', callback_data='order_diag1_no')
        markup.add(button1, button2)
        bot.edit_message_text(dialog_text, call.message.chat.id, call.message.id, reply_markup=markup)

    if call.data == "order_diag1_yes":

        dialog_text = "На сколько месяцев Вам требуется аренда?"
        dialog_text += "\n\n"
        dialog_text += "Текущие данные заказа:\n"
        dialog_text += "Вес и объём - уточним позднее"

        markup = InlineKeyboardMarkup()
        markup.row_width = 6
        button01 = InlineKeyboardButton('1', callback_data='order_months_01')
        button02 = InlineKeyboardButton('2', callback_data='order_months_02')
        button03 = InlineKeyboardButton('3', callback_data='order_months_03')
        button04 = InlineKeyboardButton('4', callback_data='order_months_04')
        button05 = InlineKeyboardButton('5', callback_data='order_months_05')
        button06 = InlineKeyboardButton('6', callback_data='order_months_06')
        button07 = InlineKeyboardButton('7', callback_data='order_months_07')
        button08 = InlineKeyboardButton('8', callback_data='order_months_08')
        button09 = InlineKeyboardButton('9', callback_data='order_months_09')
        button10 = InlineKeyboardButton('10', callback_data='order_months_10')
        button11 = InlineKeyboardButton('11', callback_data='order_months_11')
        button12 = InlineKeyboardButton('12', callback_data='order_months_12')
        markup.add(button01, button02, button03, button04, button05, button06,
                   button07, button08, button09, button10, button11, button12)
        bot.edit_message_text(dialog_text, call.message.chat.id, call.message.id, reply_markup=markup)

    if "order_months" in call.data:

        duration = int(call.data.split("_")[-1])
        dialog_text = "Вам помочь с доставкой, или Вы доставите вещи самостоятельно?"
        dialog_text += "\n\n"
        dialog_text += "Текущие данные заказа:\n"
        dialog_text += "Вес и объём - уточним позднее\n"
        dialog_text += f"Длительность аренды - {duration} мес."

        markup = InlineKeyboardMarkup()
        markup.row_width = 1
        button1 = InlineKeyboardButton('Да, организуйте доставку сами', callback_data='order_delivery_yes')
        button2 = InlineKeyboardButton('Нет, я доставлю', callback_data='order_delivery_time')
        markup.add(button1, button2)
        bot.edit_message_text(dialog_text, call.message.chat.id, call.message.id, reply_markup=markup)

    if call.data == "order_delivery_yes":

        dialog_text = "Хорошо. Напишите в чат адрес, от куда надо будет забрать вещи."
        dialog_text += "\n\n"
        dialog_text += "Текущие данные заказа:\n"
        dialog_text += "Вес и объём - уточним позднее\n"
        dialog_text += f"Длительность аренды - мес."

        markup = InlineKeyboardMarkup()
        markup.row_width = 1
        button1 = InlineKeyboardButton('Хорошо', callback_data='order_delivery_time')
        markup.add(button1)
        bot.edit_message_text(dialog_text, call.message.chat.id, call.message.id, reply_markup=markup)

    if call.data == "order_delivery_time":

        dialog_text = "Определите время"
        dialog_text += "\n\n"
        dialog_text += "Текущие данные заказа:\n"
        dialog_text += "Вес и объём - уточним позднее\n"
        dialog_text += f"Длительность аренды - мес."

        markup = InlineKeyboardMarkup()
        markup.row_width = 1
        button1 = InlineKeyboardButton('Хорошо', callback_data='order_delivery_yes')
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
