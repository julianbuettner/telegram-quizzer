import telegram
from questioncataloguing import Catalogue
from ..emoji import emojis
from ..decorators import patch_telegram_action
from ..conversationutils import (
    fallback_respond,
    cancle_handler,
)
from telegram.ext import (
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    Filters,
)
from .statistics import get_stat_handler
from .ask_mode import get_mode_handler
from .ask_section import get_section_handler
from .ask_settings import (
    get_settings_handler_lection,
    get_settings_handler_mode,
    edit_settings,
)
from .handle_answer import (
    get_handle_answer_callback,
    get_handle_answer_text,
    get_handle_answer_voice,
)
from .continue_or_explanation import (
    get_continue,
    get_explanation,
    get_continue_text,
)

@patch_telegram_action
def nothing(respond):
    respond('Okay. Katalog-Programm abgebrochen.')
    return ConversationHandler.END


def get_start_handler(catalogue: Catalogue, start_command):
    text = (
        'Das ist das Abfrageprogramm für den Fragenbogen {fragebogen}.\n'
        '{clipboard}{pen}\n'
        'Im Fragebogen liegen hat die folgende Lektionen:\n\n'
    ).format(
        clipboard=emojis.clipboard,
        fragebogen=catalogue.name,
        pen=emojis.fountain_pen
    )

    for section in catalogue.get_all_sections():
        text += '{emoji} {name}\n'.format(emoji=emojis.sunflower, name=section.name)

    text += '\nWas möchtest du tun?'
    choices = [
        [telegram.InlineKeyboardButton('Statistiken anzeigen', callback_data='stat')],
        [telegram.InlineKeyboardButton('Abfrage starten', callback_data='abfr')],
        [telegram.InlineKeyboardButton('Abbrechen', callback_data='cancel')],
    ]

    @patch_telegram_action
    def f(respond, chat_dict, delete_me):
        r = respond(text, reply_markup=telegram.InlineKeyboardMarkup(choices))
        delete_me.append(r.message_id)
        return 'action_choice'
    

    return ConversationHandler(
        entry_points=[
            CommandHandler(start_command, f),
            CallbackQueryHandler(f, pattern='back_to_intro_{}'.format(catalogue.id)),
            #CallbackQueryHandler(get_stat_handler(catalogue), pattern='stat_{}'.format(catalogue.id)),
            #CallbackQueryHandler(get_action_choice_handler(catalogue), pattern='abfr_{}'.format(catalogue.id)),
        ],
        states={
            'action_choice': [
                CallbackQueryHandler(nothing, pattern='cancel'),
                CallbackQueryHandler(get_stat_handler(catalogue), pattern='stat'),  # ENDs
                CallbackQueryHandler(get_mode_handler(catalogue), pattern='abfr'),
            ],
            'mode_choice': [
                CallbackQueryHandler(get_settings_handler_mode(catalogue), pattern='h100'),
                CallbackQueryHandler(get_section_handler(catalogue)),
            ],
            'lection_choice': [
                CallbackQueryHandler(get_settings_handler_lection(catalogue)),   
            ],
            'handle_answer': [
                CallbackQueryHandler(edit_settings, pattern='settings_toggle'),
                CallbackQueryHandler(get_handle_answer_callback(catalogue)),
                MessageHandler(Filters.text, get_handle_answer_text(catalogue)),
                MessageHandler(Filters.voice, get_handle_answer_voice(catalogue)),
            ],
            'continue_or_explanation': [
                CallbackQueryHandler(edit_settings, pattern='settings_toggle'),
                CallbackQueryHandler(get_continue(catalogue), pattern='continue'),
                CallbackQueryHandler(get_explanation(catalogue), pattern='explanation'),
                MessageHandler(Filters.all, get_continue_text(catalogue)),
            ]
            # CallbackQueryHandler(edit_settings, pattern='settings_toggle'),
        },
        fallbacks=[
            cancle_handler(),
            fallback_respond(),
        ]
    )

