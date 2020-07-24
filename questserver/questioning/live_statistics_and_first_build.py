import telegram
from threading import Thread
from questioncataloguing import Catalogue
from ..client import Client
from ..decorators import patch_telegram_action
from ..emoji import emojis
from .ask_mode import MODUS_TABLE
from time import time, sleep
from random import shuffle


def get_stat_text(chat_dict):
    diff = time() - chat_dict['start_time']

    tar = ''
    if chat_dict['mode'] == 'tar':
        tar = '(Runde {})'.format(chat_dict['round'])

    text = (
        '{tree} {mode}\n'
        '{stopwatch} Verbrauchte Zeit: {min:0>2}:{sec:0>2}min\n'
        '{questionmark} Beantwortet {q}/{q_max} {tar}'
    ).format(
        tree=emojis.tree,
        mode=MODUS_TABLE[chat_dict['mode']][0],
        stopwatch=emojis.stop_watch,
        min=int(diff / 60),
        sec=int(diff % 60),
        questionmark=emojis.grey_questionmark,
        q=len(chat_dict['answers']),
        q_max=chat_dict['q_max'],
        tar=tar,
    )
    return text


def _updater(chat_dict, message_id, edit):
    def f():
        txt = get_stat_text(chat_dict)
        edit(message_id, txt)
    return f

def update_task(updater, chat_dict):
    while True:
        if chat_dict.get('stop_live_statistics', None):
            print('[Stop live statistics]')
            return
        if time() - chat_dict['start_time'] > 3600:
            print('[Live statistics timeout]')
            return
        updater()
        sleep(1 - (time() - int(time())))


def get_live_statistics_and_first_build(catalogue: Catalogue):

    # Will not be called by conversation handler
    # Will be called from ask_settings
    def f(respond, chat_dict, chat_id, edit):
        a = Client(chat_id, catalogue)
        if chat_dict['mode'] in ['lection', 'tar']:
            chat_dict['unanswered_questions'] = catalogue.get_section(
                section_id=chat_dict['lection']
            ).get_all_questions()
        elif chat_dict['mode'] == 'h100':
            chat_dict['unanswered_questions'] = a.get_hardest(
                sections=catalogue.get_all_sections(),
                limit=100
            )
        elif chat_dict['mode'] == 'h20_lection':
            chat_dict['unanswered_questions'] = a.get_hardest(
                sections=[catalogue.get_section(section_id=chat_dict['lection'])],
                limit=20
            )
        else:
            respond('Massive error. Stacktrace generated.')
            assert False

        chat_dict['q_max'] = len(chat_dict['unanswered_questions'])
        chat_dict['answers'] = []  # (q: Question, score: float)

        if chat_dict['mode'] == 'tar':
            chat_dict['round'] = 1
            chat_dict['questions_to_do'] = []

        shuffle(chat_dict['unanswered_questions'])

        chat_dict['start_time'] = time()

        r = respond(get_stat_text(chat_dict))
        chat_dict['live_statistics_updater'] = _updater(
            chat_dict, r.message_id, edit
        )
        chat_dict['live_statistics_thread'] = Thread(
            target=update_task,
            args=(chat_dict['live_statistics_updater'], chat_dict)
        )
        chat_dict['live_statistics_thread'].start()

        chat_dict['chat_id'] = chat_id
        

    return f
