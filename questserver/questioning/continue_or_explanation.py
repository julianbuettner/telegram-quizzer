import telegram
from telegram.ext import (
    ConversationHandler
)
from time import time
from random import shuffle
from questioncataloguing import Catalogue
from ..client import Client
from ..decorators import patch_telegram_action
from ..emoji import emojis
from .ask_question import get_ask_question_handler


def _generate_endcard(chat_dict):
    diff = time() - chat_dict['start_time']

    max_points = 0
    scored = 0
    for q, score in chat_dict['answers']:
        max_points += q.points
        scored += score

    t = (
        '{celebrate} Fertig! {celebrate}\n'
        '{stopwatch} Benötigte Zeit: {min:0>2}:{sec:0>2}min\n'
        '{red_circle} Du hast {s:<3.3}/{p} Punkte erreicht.'
    ).format(
        celebrate=emojis.celebrate,
        stopwatch=emojis.stop_watch,
        min=int(diff / 60),
        sec=int(diff % 60),
        red_circle=emojis.red_circle,
        s=float(scored),
        p=float(max_points),
    )
    return t


def get_continue(c: Catalogue, patched=True):
    ask_question_handler = get_ask_question_handler(c)

    def f(respond, chat_dict, delete_me):
        if not chat_dict['unanswered_questions']:
            if chat_dict['mode'] == 'tar' and chat_dict.get('questions_to_do'):
                chat_dict['unanswered_questions'] = chat_dict['questions_to_do']
                chat_dict['questions_to_do'] = []
                shuffle(chat_dict['questions_to_do'])
                chat_dict['round'] += 1
            else:
                # Endcard
                chat_dict['stop_live_statistics'] = True
                respond(_generate_endcard(chat_dict))
                chat_dict['live_statistics_thread'].join()

                a = Client(chat_dict['chat_id'], catalogue=c)
                a.enter_run(
                    section_id=chat_dict.get('lection'),
                    gamemode=chat_dict['mode'],
                    start=chat_dict['start_time'],
                    duration=time() - chat_dict['start_time'],
                )

                return ConversationHandler.END

        ask_question_handler(chat_dict, respond, delete_me)

        return 'handle_answer'

    if patched:
        return patch_telegram_action(f)
    return f


def get_continue_text(c: Catalogue):
    continue_handler = get_continue(c, patched=False)

    @patch_telegram_action
    def f(message_id, delete_me, respond, chat_dict):
        delete_me.append(message_id)
        return continue_handler(respond, chat_dict, delete_me)
    
    return f


def get_explanation(c: Catalogue):
    @patch_telegram_action
    def f(chat_dict, respond, delete_me):
        q = chat_dict['current_question']

        for photo in q.explanation_attachments:
            with open('{}/{}'.format(c.mediadir, photo), 'rb') as f:
                r = respond('', photo=f, do_delete=False)
                delete_me.append(r.message_id)

        text = 'Erklärung\n\n'
        if q.explanation:
            text += q.explanation

        reply_markup = telegram.InlineKeyboardMarkup(
            [[telegram.InlineKeyboardButton('Weiter', callback_data='continue')]]
        )
        r = respond(text, reply_markup=reply_markup, do_delete=False)
        delete_me.append(r.message_id)

        return 'continue_or_explanation'  # but only continue button

    return f