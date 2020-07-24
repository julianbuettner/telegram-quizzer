from datetime import datetime
from os import makedirs

makedirs('./log', exist_ok=True)


class Colorized:
    def __init__(self, text):
        self.text = str(text)
    def __getattr__(self, color):
        colortable = {
            'red': '0;31',
            'light_red': '1;31',
            'green': '0;32',
            'light_green': '1;32',
            'blue': '0;34',
            'light_blue': '1;34',
            'grey': '1;30',
            'yellow': '1;33'
        }
        r = '\033[{color}m{text}\033[0m'.format(
            color=colortable[color],
            text=self.text
        )
        return r


def string_yellow_none_grey(x):
    if x is None:
        return Colorized(x).grey
    return Colorized(x).yellow


def print_write(string, chat_id):
    logfile_path = 'log/user_{}.log'.format(
        chat_id
    )
    with open(logfile_path, 'a') as f:
        f.write(string)
    print(string, end='', flush=True)



def log_incoming_message(user, message):
    msg = Colorized('[Unknown message type]').red
    if getattr(message, 'text', None):
        msg = Colorized(message.text).green
    elif getattr(message, 'sticker', None):
        msg = '{} {}'.format(Colorized('[sticker]').red, message.sticker.emoji)
    else:
        print('TODO', message)

    s = '[{datetime}] [{fname:<7} @{uname:<7} {lname:<5}] {msg}\n'
    s = s.format(
        fname=string_yellow_none_grey(user.first_name),
        uname=string_yellow_none_grey(user.username),
        lname=string_yellow_none_grey(user.last_name),
        datetime=Colorized(datetime.now().strftime('%Y-%M-%d %H:%M:%S')).blue,
        msg=msg,
    )
    print_write(s, message.chat.id)


def log_incoming_voice(user, stt, message):
    voice = Colorized('[Voice]').red
    text = Colorized('[Not detected]').red
    if stt.text:
        text = Colorized(stt.text).green
    
    s = '[{datetime}] [{fname:<7} @{uname:<7} {lname:<5}] {voice} {txt}\n'
    s = s.format(
        fname=string_yellow_none_grey(user.first_name),
        uname=string_yellow_none_grey(user.username),
        lname=string_yellow_none_grey(user.last_name),
        datetime=Colorized(datetime.now().strftime('%Y-%M-%d %H:%M:%S')).blue,
        voice=voice,
        txt=text,
    )
    print_write(s, message.chat.id)


def log_incoming_callback(user, callback_query):
    msg = (
        Colorized('<= ').yellow +
        Colorized(callback_query.data).blue
    )

    s = '[{datetime}] [{fname:<7} @{uname:<7} {lname:<5}] {msg}\n'
    s = s.format(
        fname=string_yellow_none_grey(user.first_name),
        uname=string_yellow_none_grey(user.username),
        lname=string_yellow_none_grey(user.last_name),
        datetime=Colorized(datetime.now().strftime('%Y-%M-%d %H:%M:%S')).blue,
        msg=msg,
    )
    print_write(s, callback_query.message.chat.id)


def log_response(message, user):
    text = Colorized('[Unknown message type]').grey
    if getattr(message, 'text', None):
        text = Colorized(message.text).light_green.replace(
            '\n', '\n\t\t'
        )
    elif getattr(message, 'description', None):
        text = Colorized(message.description).light_green
    else:
        print('TODO', message)

    s = '[{datetime}] [{arrow}] {msg}\n'.format(
        datetime=Colorized(datetime.now().strftime('%Y-%M-%d %H:%M:%S')).blue,
        arrow=Colorized('   =>   ').yellow,
        msg=text,
    )
    print_write(s, message.chat.id)
