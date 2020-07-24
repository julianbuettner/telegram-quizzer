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
from ..conversationutils import abcd_inline_buttons, abcd
from random import shuffle


def _get_text_and_reply_markup_from_question(q: _Question, chat_dict):
    if isinstance(q, (RegexQuestion, EstimationQuestion, AudioDictate)):
        return q.question, None
    
    answers = [q.right_answer] + q.wrong_answers
    shuffle(answers)
    chat_dict['multiple_choice_answers_in_order'] = answers

    question_text = q.question + '\n\n'
    chars = abcd(len(answers))
    for i in range(len(answers)):
        a_text = '{diamond} {char} - {answer}\n\n'.format(
            diamond=emojis.small_orange_diamond,
            char=chars[i],
            answer=answers[i]
        )
        question_text += a_text
        if answers[i] == q.right_answer:
            chat_dict['expected_letter'] = chars[i]
            print('Richtige Antwort:', chars[i].upper())
    return question_text, telegram.InlineKeyboardMarkup(abcd_inline_buttons(len(answers)))


def get_ask_question_handler(c: Catalogue):

    # Will be used directly
    def f(chat_dict, respond, delete_me):
        q: _Question = chat_dict['unanswered_questions'].pop()
        chat_dict['current_question'] = q

        delete_me_later = []

        for photo in q.question_attachments:
            with open('{}/{}'.format(c.mediadir, photo), 'rb') as f:
                r = respond('', photo=f)
                delete_me_later.append(r.message_id)

        text, reply_markup = _get_text_and_reply_markup_from_question(q, chat_dict)
        r = respond(text, reply_markup=reply_markup)
        delete_me += delete_me_later + [r.message_id]

    return f
