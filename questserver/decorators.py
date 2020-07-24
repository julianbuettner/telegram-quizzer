import telegram
import telegram.ext
from io import BytesIO
from requests import get
#from .tts import tts
from .log import (
    log_incoming_message,
    log_incoming_callback,
    log_incoming_voice,
    log_response,
)


def _respond(context, chat_id, from_user, delete_me):
    def do_deletion():
        while delete_me:
            msg_id = delete_me.pop()
            try:
                context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
            except telegram.TelegramError:
                pass

    
    def f(txt, **f_kwargs):
        do_delete = True
        if f_kwargs.get('do_delete') is not None:
            do_delete = f_kwargs.pop('do_delete')
        if f_kwargs.get('photo'):
            photo = f_kwargs.get('photo')
            m = context.bot.send_photo(
                chat_id=chat_id,
                photo=photo,
                caption=txt[:1024])
            if do_delete:
                do_deletion()
            return m
        # TODO Audio
        # TODO Video
        res = context.bot.send_message(
            chat_id=chat_id,
            text=txt,
            **f_kwargs)
        log_response(res, from_user)
        if do_delete:
            do_deletion()
        return res
    return f


def _delete(context, chat_id):
    def f(message_id):
        try:
            context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        except telegram.TelegramError:
            pass
    return f


def _edit(context, chat_id):
    def f(message_id, new_text, **kwargs):
        try:
            context.bot.edit_message_text(new_text, chat_id=chat_id, message_id=message_id, **kwargs)
        except telegram.TelegramError:
            pass
    return f


def _commit_callback(context, callback_id):
    def f(**kwargs):
        context.bot.answer_callback_query(callback_id, **kwargs)
    return f


def _voice_to_file(context, file_id):
    f = context.bot.get_file(file_id)
    r = get(f.file_path)
    return BytesIO(r.content)


def patch_telegram_action(old_function):

    def new_function(update, context):
        user = update._effective_user
        name = update._effective_user.first_name
        username = update._effective_user.username

        voice_stt = None

        if update.message is not None:
            if update.message.voice:
                # Voice
                raise ValueError('Audio to text TODO')  # TODO
                '''
                f = _voice_to_file(context, update.message.voice.file_id)
                speech_to_text = tts(f, de=True)
                voice_stt = speech_to_text
                f.close()
                log_incoming_voice(user, speech_to_text, update.message)
                '''
            else:
                # Text
                log_incoming_message(user, update.message)
        elif update.callback_query:
            log_incoming_callback(user, update.callback_query)
        else:
            print('TODO')
            print(update)

        if not context.chat_data.get('_delete_me'):
            context.chat_data['_delete_me'] = []

        kwargs = {
            'update': update,
            'context': context,
            'bot': context.bot,
            'username': username,
            'user': user,
            'name': name,
            'chat_dict': context.chat_data,
            'delete_me': context.chat_data['_delete_me'],
            'voice_stt': voice_stt,
        }

        if update.message:
            kwargs['message_id'] = update.message.message_id
            kwargs['text'] = update.message.text
            kwargs['chat_id'] = update.message.chat.id
            kwargs['text'] = update.message.text

        if update.callback_query:
            kwargs['original_message_id'] = update.callback_query.message.message_id
            kwargs['commit_callback'] = _commit_callback(context, update.callback_query.id)
            kwargs['callback_data'] = update.callback_query.data
            kwargs['chat_id'] = update._effective_chat.id

        kwargs['respond'] = _respond(
            context,
            kwargs['chat_id'],
            user,
            kwargs['delete_me'])
        kwargs['delete'] = _delete(context, kwargs['chat_id'])
        kwargs['edit'] = _edit(context, kwargs['chat_id'])

        filtered_kwargs = {}
        old_function_params = old_function.__code__.co_varnames[:old_function.__code__.co_argcount]

        for key, value in kwargs.items():
            if key in old_function_params:
                filtered_kwargs[key] = value
        res = old_function(**filtered_kwargs)
        return res

    return new_function
