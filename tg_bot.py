import os
import logging
from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                        ConversationHandler)
import fetch_quiz_content
import random
import redis


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)
R = redis.Redis(
    host=os.environ.get['REDIS_HOST'],
    port=os.environ.get['REDIS_PORT'],
    db=0,
    password=os.environ.get['REDIS_PASWORD'],
    decode_responses=True
    )
Q_A_PAIRS = fetch_quiz_content.main()
NEW_Q, ANSWER = range(2)

def start(update, context):

    custom_kayboard = [[KeyboardButton('Новый вопрос'),
                        KeyboardButton('Сдаться')],
                        [KeyboardButton('Мой счёт')]]
    reply_markup = ReplyKeyboardMarkup(custom_kayboard)
    update.message.reply_text('Hi!', reply_markup=reply_markup)
    return NEW_Q


def help(update, context):

    help_text = 'Начать игру можно командой /start.\nЗакончить командой /end'
    update.message.reply_text(help_text)

def adjust_score(u_id, adj):

    score_key = 'Score_%s'%(u_id)
    current_score = R.get(score_key)
    if current_score is not None:
        new_score = int(current_score) + adj
        R.set(score_key, new_score)
    else:
        R.set(score_key, adj)


def fetch_new_q(update, context):

    user = update.message.from_user
    question, answer = random.choice(list(Q_A_PAIRS.items()))
    update.message.reply_text(question)
    R.set(user.id, question)
    return ANSWER

def analize_answer(update, context):

    user = update.message.from_user
    users_question = R.get(user.id)
    users_answer = update.message.text
    right_answer = Q_A_PAIRS[users_question]
    R.delete(user.id)

    if users_answer in right_answer:
        resulting_text = 'И это ... ПРАВИЛЬНЫЙ ОТВЕТ!!!'
        score_adjustment = 10
    else:
        resulting_text = 'И это ... ПРОВАЛ БРАЧО!!!'
        score_adjustment = -10
    update.message.reply_text(resulting_text)
    adjust_score(user.id, score_adjustment)
    return NEW_Q


def give_up(update, context):
    user = update.message.from_user
    users_question = R.get(user.id)
    if users_question is None:
        update.message.reply_text('Рано сдаваться!')
    else:
        right_answer = Q_A_PAIRS[users_question]
        sad_text = 'Очень жаль, правильным ответом был: %s'%(right_answer)
        update.message.reply_text(sad_text)
        R.delete(user.id)
        score_adjustment = -5
        adjust_score(user.id, score_adjustment)
        return NEW_Q


def fetch_score(update, context):

    user = update.message.from_user
    score_key = 'Score_%s'%(user.id)
    current_score = R.get(score_key)
    if current_score is None:
        current_score = 0
    current_score_text = 'На данный момент, у вас %s очков!'%(current_score)
    update.message.reply_text(current_score_text)


def bad_new_q(update, context):

    update.message.reply_text('Надо ответить на предыдущий вопрос либо сдаться')


def error(update, context):

    logger.warning('Update "%s" caused error "%s"', update, context.error)


def end_this_game(update, context):

    reply_markup = ReplyKeyboardRemove()
    update.message.reply_text('Буду ждать новую игру!', reply_markup=reply_markup)
    return ConversationHandler.END


def english(update, context):

    update.message.reply_text('В этом вопросе вам знания английского ни к чему!')


def main():

    tg_token = os.environ.get['TG_TOKEN']
    updater = Updater(tg_token, use_context=True)

    dp = updater.dispatcher
    dp.add_handler(CommandHandler('help', help))
    dp.add_handler(MessageHandler(Filters.regex('^знаю английский$'), english))
    dp.add_handler(MessageHandler(Filters.regex('^Мой счёт$'), fetch_score))
    conv_hand = ConversationHandler(
    entry_points=[CommandHandler('start', start)],

    states = {
        NEW_Q: [MessageHandler(Filters.regex('^Новый вопрос$'), fetch_new_q),
                MessageHandler(Filters.regex('^Сдаться$'), give_up)],
        ANSWER: [MessageHandler(Filters.regex('^Сдаться$'), give_up),
                 MessageHandler(Filters.regex('^Новый вопрос$'), bad_new_q),
                 MessageHandler(Filters.text, analize_answer)]

    },
    fallbacks=[CommandHandler('end', end_this_game)]
    )
    dp.add_handler(conv_hand)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
