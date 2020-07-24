from questioncataloguing import catalogue_from_dict
from json import loads
import telegram
from .decorators import patch_telegram_action
from .questioning import get_start_handler
from .config import (
    BOTTOKEN,
    WELCOME,
    CATALOGUESPECIFIERS,
    CatalogueSpecifier,
)
from telegram.ext import (
    CommandHandler,
    ConversationHandler,
    Filters,
    MessageHandler,
    Updater,
)


@patch_telegram_action
def start_message(respond):
    respond(WELCOME)


@patch_telegram_action
def help_command(respond):
    text = '/help\n\n'
    for cs in CATALOGUESPECIFIERS:
        text += '/{} - {}\n\n'.format(
            cs.command, cs.description
        )

    respond(text)


@patch_telegram_action
def telegram_unexpecte_text(respond):
    respond('Du musst erst ein Programm starten.\n'
        'Siehe /help für verüfugbare Befehle.',
        reply_markup=telegram.ReplyKeyboardRemove())



def error_handler(update, context):
    from subprocess import run
    import traceback
    from datetime import datetime

    try:
        raise context.error
    except:
        tb = traceback.format_exc()

    print(tb)
    print('ERROR')

    run(['mkdir', '-p', 'tracebacks'], check=True)
    with open('tracebacks/' + str(datetime.now().timestamp()), 'w') as f:
        f.write('Error occured at {}:\n'.format(datetime.now()))
        f.write(tb)

    context.bot.send_message(
        text='Der Bot ist gecrasht! Eine Fehlermeldung wurde '
        'auf dem Server gerneriert und wird bei Bemerken analysiert und '
        'eventuell demnächst gefixt!',
        chat_id=update.message.chat.id)
    return ConversationHandler.END


def get_command_and_catalogue(catalogue_specifier: CatalogueSpecifier):
    with open(catalogue_specifier.path) as f:
        catalogue = catalogue_from_dict(loads(f.read()))
    if catalogue_specifier.mediadir:
        catalogue.mediadir = catalogue_specifier.mediadir
    return catalogue_specifier.command, catalogue


def build_updater():
    print('Compile bot')
    updater = Updater(
        token=BOTTOKEN,
        use_context=True,
        workers=4,
        persistence=None
    )

    updater.dispatcher.add_handler(
        CommandHandler('help', help_command)
    )

    updater.dispatcher.add_handler(
        CommandHandler('start', start_message)
    )
    
    for cs in CATALOGUESPECIFIERS:
        command, catalogue = get_command_and_catalogue(cs)
        updater.dispatcher.add_handler(
           get_start_handler(catalogue, command) 
        )
    
    updater.dispatcher.add_handler(
        MessageHandler(Filters.all, telegram_unexpecte_text)
    )

    updater.dispatcher.add_error_handler(error_handler)

    return updater
