import telegram
from questioncataloguing import (
    Catalogue,
    _Question,
    MultipleChoiceQuestion,
    RegexQuestion,
    EstimationQuestion,
    AudioDictate,
)
from ..client import Client
from ..decorators import patch_telegram_action
from ..emoji import emojis
from ..conversationutils import abcd
#from .ask_question import get_ask_question_handler
from .continue_or_explanation import get_continue


def text_to_float(text):
    text = text.replace(',', '.')
    try:
        f = float(text)
        return f
    except ValueError:
        return


def get_solution_text_and_markup(q: _Question, score, chat_dict, client_answer):
    buttons = [
        [telegram.InlineKeyboardButton('Weiter', callback_data='continue')]
    ]
    if hasattr(q, 'explanation'):
        if q.explanation or q.explanation_attachments:
            buttons.append(
                [telegram.InlineKeyboardButton('Erklärung', callback_data='explanation')]
            )
    if isinstance(q, EstimationQuestion):
        t =  (
            '{qm} {question}\n\n'
            '{check} {solution}\n'
            '{arrow} {client_answer}\n'
            'Dein Score ist {s:<3.3}/{p} Points.'
        ).format(
            qm=emojis.grey_questionmark,
            question=q.question,
            check=emojis.green_check,
            solution=q.right_answer,
            arrow=emojis.arrow_forward,
            client_answer=client_answer,
            s=score,
            p=q.points
        )
        return t, telegram.InlineKeyboardMarkup(buttons)
    if isinstance(q, RegexQuestion):
        t = (
            '{qm} {question}\n\n'
            '{check} {solution}'
        ).format(
            qm=emojis.grey_questionmark,
            question=q.question,
            check=emojis.green_check,
            solution=q.answer,
        )
        if not q.match(client_answer):
            t += '\n{cross} {client_answer}'.format(
                cross=emojis.red_cross,
                client_answer=client_answer
            )
        return t, telegram.InlineKeyboardMarkup(buttons)
    if isinstance(q, AudioDictate):
        t = (
            '{qm} {question}\n'
            '{check} {solution}'
        ).format(
            qm=emojis.grey_questionmark,
            question=q.question,
            check=emojis.green_check,
            solution=q.right_answer,
        )
        if not q.match(client_answer):
            t += '\n{cross} {client_answer}'.format(
                cross=emojis.red_cross,
                client_answer=client_answer.title()
            )
        return t, telegram.InlineKeyboardMarkup(buttons)

    # Mutiple Choice
    t = q.question + '\n\n'
    answers_in_order = chat_dict['multiple_choice_answers_in_order']
    chars = abcd(len(answers_in_order))
    for i in range(len(answers_in_order)):
        diamond = emojis.small_orange_diamond
        if chars[i] == client_answer.upper():
            diamond = emojis.red_cross
        if chars[i] == chat_dict['expected_letter']:
            diamond = emojis.green_check
        a_text = '{diamond} {char} - {answer}\n\n'.format(
            diamond=diamond,
            char=chars[i],
            answer=answers_in_order[i]
        )
        t += a_text
    return t, telegram.InlineKeyboardMarkup(buttons)



def _get_handle_answer_after_scoring(c: Catalogue):
    continue_handler = get_continue(c, patched=False)

    def f(chat_id, chat_dict, score, respond, delete_me, client_answer):
        a = Client(chat_id, c)
        q: _Question = chat_dict['current_question']

        # Enter into database and in chat_dict
        a.enter_score(q, score=score)
        chat_dict['answers'].append((q, score))

        chat_dict['live_statistics_updater']()  # Update live stats

        correct = (score > 0.5 * q.points)

        if chat_dict['mode'] == 'tar' and not correct:
            chat_dict['questions_to_do'].append(q)
        
        if correct and chat_dict['settings']['continue_if_correct']:
            return continue_handler(respond, chat_dict, delete_me)

        # Send solution
        text, reply_markup = get_solution_text_and_markup(q, score, chat_dict, client_answer)
        r = respond(text, reply_markup=reply_markup)
        delete_me.append(r.message_id)

        return 'continue_or_explanation'

    return f


def get_handle_answer_callback(c: Catalogue):
    handle_answer_after_scoring = _get_handle_answer_after_scoring(c)

    @patch_telegram_action
    def f(callback_data, chat_dict, respond, delete_me, chat_id):
        q: _Question = chat_dict['current_question']
        if callback_data.upper() not in abcd(len(q.wrong_answers) + 1) or not isinstance(q, MultipleChoiceQuestion):
            r = respond('Diese Buttons kannst du im Moment nicht nutzen', do_delete=False)
            delete_me.append(r.message_id)
            return 'handle_answer'

        correct = callback_data.lower() == chat_dict['expected_letter'].lower()
        score = 0
        if correct:
            score = q.points

        return handle_answer_after_scoring(chat_id, chat_dict, score, respond, delete_me, client_answer=callback_data)

    return f


def get_handle_answer_text(c: Catalogue):
    handle_answer_after_scoring = _get_handle_answer_after_scoring(c)

    @patch_telegram_action
    def f(chat_id, chat_dict, text, delete_me, message_id, delete, respond):
        q: _Question = chat_dict['current_question']
        delete_me.append(message_id)

        score = 0
        if isinstance(q, RegexQuestion):
            q: RegexQuestion = q
            if q.match(text.lower()):
                score = q.points

        elif isinstance(q, AudioDictate):
            r = respond('Bitte sende eine Voicenachricht!')
            delete_me.append(message_id)
            delete_me.append(r.message_id)
            return 'handle_answer'

        elif isinstance(q, EstimationQuestion):
            q: EstimationQuestion = q
            if not text_to_float(text):
                r = respond(
                    '"{}" ist keine Zahl. Bitte gebe eine Zahl an.'.format(text),
                    do_delete=False
                )
                delete_me.append(r.message_id)
                return 'handle_answer'
            score = q.evaluate_score(text_to_float(text))

        elif isinstance(q, MultipleChoiceQuestion):
            q: MultipleChoiceQuestion = q
            if not text.upper() in abcd(len(q.wrong_answers) + 1):
                r = respond(
                    '"{}" ist keine valide Antwort.'.format(text),
                    do_delete=False
                )
                delete_me.append(r.message_id)
                return 'handle_answer'
            if text.lower() == chat_dict['expected_letter'].lower():
                score = q.points

        return handle_answer_after_scoring(chat_id, chat_dict, score, respond, delete_me, client_answer=text)


    return f


def get_handle_answer_voice(c: Catalogue):
    handle_answer_after_scoring = _get_handle_answer_after_scoring(c)

    @patch_telegram_action
    def f(chat_id, chat_dict, voice_stt, delete_me, message_id, delete, respond):
        a = Client(chat_id, c)
        q: _Question = chat_dict['current_question']
        delete_me.append(message_id)

        if not isinstance(q, AudioDictate):
            t = (
                'Eine Voicenachricht wurde nicht erwartet.\n'
                'Bitte antworte wie angefragt.'
            )
            r = respond(t)
            delete_me.append(r.message_id)
            return 'handle_answer'

        if not voice_stt.text:
            t = (
                'Die Spracherkennung hat leider nicht funkioniert.\n'
                'Bitte probiere es erneut. Sollte das Problem bestehen bleiben'
                'melde dies bitte.'
            )
            if voice_stt.error_code:
                t += 'Error code: ' + voice_stt.error_code
            r = respond(t)
            delete_me.append(r.message_id)
            return 'handle_answer'

        score = 0
        if q.match(voice_stt.text):
            score = q.points

        return handle_answer_after_scoring(chat_id, chat_dict, score, respond, delete_me, client_answer=voice_stt.text)

    return f
