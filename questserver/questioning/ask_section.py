import telegram
from questioncataloguing import Catalogue
from ..client import Client
from ..decorators import patch_telegram_action
from ..emoji import emojis


def _get_section_buttons(c: Catalogue, chat_id):
    a = Client(chat_id, c)

    buttons = []
    for section in c.get_all_sections():
        text = '{name} {perc}% ({count} Fragen)\n'.format(
            name=section.name,
            perc=int(a.get_section_score(section) * 100),
            count=len(section.get_all_questions()),
        )
        buttons.append([telegram.InlineKeyboardButton(text, callback_data=section.id)])
    return buttons


def get_section_handler(c: Catalogue):

    @patch_telegram_action
    def f(respond, delete_me, callback_data, chat_dict, chat_id):
        chat_dict['mode'] = callback_data

        text = (
            'Über welche Lektion möchtest du abgefragt werden?'
        )
        r = respond(text, reply_markup=telegram.InlineKeyboardMarkup(_get_section_buttons(c, chat_id)))
        delete_me.append(r.message_id)
        return 'lection_choice'
    return f
