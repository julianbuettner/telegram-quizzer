import telegram
from telegram.ext import (MessageHandler, ConversationHandler,
    Filters, CommandHandler)
from ..emoji import progress_to_machine_emoji
from ..decorators import patch_telegram_action
from questioncataloguing import Catalogue
from ..client import Client
from datetime import datetime
from .ask_mode import MODUS_TABLE


def get_stat_handler(catalogue: Catalogue):
    @patch_telegram_action
    def f(respond, chat_id, delete_me):
        a = Client(chat_id, catalogue)
        text = 'Hier dein Fortschritt:\n\n'
        for section in catalogue.get_all_sections():
            progress = a.get_section_score(section)
            text += '{emoji} {perc:<.3}% {sn}\n'.format(
                emoji=progress_to_machine_emoji(progress),
                perc=float(progress * 100),
                sn=section.name
            )
        text += '\n\nDurchläufe:\n'

        runs = a.get_run_scorediffs()
        if not runs:
            text += 'Es scheint noch keine vollständigen Durchläufe zu geben.'
        for run in runs:
            section_details = ''
            if run.section:
                section_details = '({name} {diff:<.3}%)'.format(
                    name=run.section.name,
                    diff=run.section_scorediff * 100,
                )
            run_text = '{date} {chart_emoji} {scorediff:<.3}% {mode} {section_details}\n'.format(
                date=datetime.fromtimestamp(run.timestamp + run.duration).strftime('%Y/%m/%d %H:%M'),
                chart_emoji='',
                scorediff=run.scorediff * 100,
                mode=MODUS_TABLE[run.mode][0],
                section_details=section_details,
            )
            text += run_text

        text += (
            '\n\nDer Fortschritt einer Lektion ist die '
            'durchschnittliche Confidence der enthaltenen Fragen.\n'
            'Die Confidence einer Frage berechnet sich aus deinen letzten 6 Antworten.\n'
            'Für mehr Infos einfach fragen.')
        reply_markup = telegram.InlineKeyboardMarkup(
            [[telegram.InlineKeyboardButton(
                'Zurück',
                callback_data='back_to_intro_{}'.format(catalogue.id))
            ]]
        )
        r = respond(text, reply_markup=reply_markup)
        delete_me.append(r.message_id)
        return ConversationHandler.END
    return f
