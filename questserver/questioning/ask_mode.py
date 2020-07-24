import telegram
from questioncataloguing import Catalogue
from ..client import Client
from ..decorators import patch_telegram_action
from ..emoji import emojis


MODUS_TABLE = {
    'lection': ('Lection Run Through', 'Ein Durchlauf in einem Fachbereich, jede Frage ein mal'),
    'h100': ('Hardest 100', 'Wiederhole die 100 (individuell) schwersten Fragen aus dem ganzen Katalog'),
    'h20_lection': ('Hardest 20 Lection', 'Wiederhole die 20 (individuell) schwersten Fragen eines Fachbereichs'),
    'tar': ('Till all right', 'Solange abgefragt werden, bis jede Frage eines Fachbereichs einmal richtig beantwortet wurde')
}


def get_available_modi(c: Catalogue):
    modi = ['lection']
    if len(c.get_all_sections()) > 1:
        modi.append('h100')
        modi.append('h20_lection')
    modi.append('tar')
    return modi


def get_mode_handler(c: Catalogue):
    buttons = []
    text = 'Der Katalog unterstützt die folgenden Modi:\n\n'
    for mode in get_available_modi(c):
        text += '{emoji} {mode} - {descr}\n\n'.format(
            emoji=emojis.plane,
            mode=MODUS_TABLE[mode][0],
            descr=MODUS_TABLE[mode][1]
        )
        buttons.append([telegram.InlineKeyboardButton(MODUS_TABLE[mode][0], callback_data=mode)])

    @patch_telegram_action
    def f(respond, delete_me):
        r = respond(text, reply_markup=telegram.InlineKeyboardMarkup(buttons))
        delete_me.append(r.message_id)
        return 'mode_choice'
    return f
       
