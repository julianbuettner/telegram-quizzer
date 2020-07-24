import telegram
from questioncataloguing import Catalogue
from ..client import Client
from ..decorators import patch_telegram_action
from ..emoji import emojis
from .live_statistics_and_first_build import get_live_statistics_and_first_build
from .ask_question import get_ask_question_handler


def get_default_settings(c: Catalogue):
    s = {
        'settings_message_id': None,
        'continue_if_correct': True,  # correct = full score
    }
    return s


def get_text_from_settings(s: dict):
    def bool_emoji(b):
        if b:
            return emojis.green_check
        return emojis.grey_dash
    text = (
        'Hier sind die aktuellen Einstellungen:\n\n'
        'Bei richtigen Antworten automatisch Fortfahren? {cic}'
    ).format(
        cic=bool_emoji(s['continue_if_correct'])
    )
    return text

_button_markup = telegram.InlineKeyboardMarkup([
    [telegram.InlineKeyboardButton(
        'Toggle Fortfahren-wenn-richtig',
        callback_data='settings_toggle_cic'
    )],
])


def get_settings_handler_lection(c: Catalogue):
    live_statistics_and_first_build = get_live_statistics_and_first_build(c)
    ask_question_handler = get_ask_question_handler(c)

    @patch_telegram_action
    def f(respond, callback_data, chat_dict, chat_id, edit, delete_me):
        chat_dict['lection'] = callback_data
        chat_dict['settings'] = get_default_settings(c)
        r = respond(get_text_from_settings(chat_dict['settings']), reply_markup=_button_markup)
        chat_dict['settings']['settings_message_id'] = r.message_id

        live_statistics_and_first_build(respond, chat_dict, chat_id, edit)

        ask_question_handler(chat_dict, respond, delete_me)

        return 'handle_answer'

    return f


def get_settings_handler_mode(c: Catalogue):
    live_statistics_and_first_build = get_live_statistics_and_first_build(c)
    ask_question_handler = get_ask_question_handler(c)

    @patch_telegram_action
    def f(respond, callback_data, chat_dict, chat_id, edit, delete_me):
        chat_dict['mode'] = callback_data
        chat_dict['settings'] = get_default_settings(c)
        r = respond(get_text_from_settings(chat_dict['settings']), reply_markup=_button_markup)
        chat_dict['settings']['settings_message_id'] = r.message_id

        live_statistics_and_first_build(respond, chat_dict, chat_id, edit)

        ask_question_handler(chat_dict, respond, delete_me)

        return 'handle_answer'

    return f


@patch_telegram_action
def edit_settings(respond, callback_data, chat_dict, edit, commit_callback):
    if callback_data == 'settings_toggle_cic':
        old = chat_dict['settings']['continue_if_correct']
        chat_dict['settings']['continue_if_correct'] = not old

    t = get_text_from_settings(chat_dict['settings'])
    edit(chat_dict['settings']['settings_message_id'], t, reply_markup=_button_markup)
    commit_callback()

