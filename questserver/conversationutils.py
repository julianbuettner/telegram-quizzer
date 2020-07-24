import telegram
from .decorators import patch_telegram_action
from telegram.ext import (Updater, MessageHandler, ConversationHandler,
    Filters, CommandHandler, CallbackQueryHandler)


def fallback_respond(text=None):
    if not text:
        text = ('Die Nachricht wurde ignoriert.\n'
        'Schreibe /cancel um das laufende Programm zu beenden.')
    @patch_telegram_action
    def f(respond, message_id, delete_me):
        r = respond(text, do_delete=False)
        delete_me.append(message_id)
        delete_me.append(r.message_id)
    h = MessageHandler(Filters.all, f)
    return h


def cancle_handler(text=None):
    if not text:
        text = 'Okay, das Programm wurde abgebrochen.'
    @patch_telegram_action
    def f(respond, chat_dict):
        if chat_dict.get('live_statistics_thread'):
            chat_dict['stop_live_statistics'] = True
            chat_dict['live_statistics_thread'].join()
        respond(text, reply_markup=telegram.ReplyKeyboardRemove())
        return ConversationHandler.END
    c = CommandHandler('cancel', f)
    return c


def fallback_disable_inline_button():
    t = ('\n\nDu befindest dich gerade in keinem Programm.\n'
        'Die Buttons dieser Nachricht wurden deaktiviert.\n'
        'Um zu sehen welche Programme es gibt schreibe /help.')
    @patch_telegram_action
    def f(delete_buttons, edit):
        delete_buttons(t)
    h = CallbackQueryHandler(f)
    return h


def abcd(length):
    r = []
    for i in range(length):
        r.append(bytes([b'A'[0]+i]).decode())
    return r


def abcd_buttons(length, line_width=2):
    assert length <= 26
    r = abcd(length)
    res = [[]]
    for c in r:
        if len(res[-1]) < line_width:
            res[-1].append(c)
        else:
            res.append([c])
    return res

def abcd_inline_buttons(length, line_width=2):
    assert length <= 26
    r = abcd(length)
    res = [[]]
    for c in r:
        b = telegram.InlineKeyboardButton(c, callback_data=c.lower())
        if len(res[-1]) < line_width:
            res[-1].append(b)
        else:
            res.append([b])
    return res
