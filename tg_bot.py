import logging
from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                        ConversationHandler)
import fetch_quiz_content
import random
import redis_db as rdb
from functools import partial
import adjust_score


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


def fetch_new_q(update, context, r):

    user = update.message.from_user
    question= random.choice(list(Q_A_PAIRS.keys()))
    update.message.reply_text(question)
    tg_user_id = 'TG_%s'%(user.id)
    r.set(tg_user_id, question)
    return ANSWER


def analyze_answer(update, context, r):

    user = update.message.from_user
    tg_user_id = 'TG_%s'%(user.id)
    users_question = r.get(tg_user_id)
    users_answer = update.message.text
    right_answer = Q_A_PAIRS[users_question]
    r.delete(tg_user_id)

    if users_answer in right_answer:
        resulting_text = 'И это ... ПРАВИЛЬНЫЙ ОТВЕТ!!!'
        score_adjustment = 10
    else:
        resulting_text = 'И это ... ПРОВАЛ БРАЧО!!!'
        score_adjustment = -10
    update.message.reply_text(resulting_text)
    adjust_score.main(tg_user_id, score_adjustment, r)
    return NEW_Q


def give_up(update, context, r):

    user = update.message.from_user
    tg_user_id = 'TG_%s'%(user.id)
    users_question = r.get(tg_user_id)
    if users_question is None:
        update.message.reply_text('Рано сдаваться!')
    else:
        right_answer = Q_A_PAIRS[users_question]
        sad_text = 'Очень жаль, правильным ответом был: %s'%(right_answer)
        update.message.reply_text(sad_text)
        r.delete(tg_user_id)
        score_adjustment = -5
        adjust_score.main(tg_user_id, score_adjustment, r)
        return NEW_Q


def fetch_score(update, context, r):

    user = update.message.from_user
    tg_user_id = 'TG_%s'%(user.id)
    score_key = 'Score_%s'%(tg_user_id)
    current_score = r.get(score_key)
    if current_score is None:
        current_score = 0
    current_score_text = 'На данный момент, у вас %s очков!'%(current_score)
    update.message.reply_text(current_score_text)


def reply_to_bad_new_q(update, context):

    update.message.reply_text('Надо ответить на предыдущий вопрос либо сдаться')


def error(update, context, logger):

    logger.warning('Update "%s" caused error "%s"', update, context.error)


def end_this_game(update, context):

    reply_markup = ReplyKeyboardRemove()
    update.message.reply_text('Буду ждать новую игру!', reply_markup=reply_markup)
    return ConversationHandler.END


def main():

    logger = logging.getLogger(__name__)
    r = rdb.connect_to_db()
    partial_fetch_score = partial(fetch_score, r=r)
    partial_give_up = partial(give_up, r=r)
    partial_analyze_answer = partial(analyze_answer, r)
    partial_fetch_new_q = partial(fetch_new_q, r=r)
    partial_error = partial(error, logger=logger)

    tg_token = os.environ.get['TG_TOKEN']
    updater = Updater(tg_token, use_context=True)

    dp = updater.dispatcher
    dp.add_error_handler(partial_error)
    dp.add_handler(CommandHandler('help', help))
    dp.add_handler(MessageHandler(Filters.regex('^Мой счёт$'), partial_fetch_score))
    conv_hand = ConversationHandler(
    entry_points=[CommandHandler('start', start)],

    states = {
        NEW_Q: [MessageHandler(Filters.regex('^Новый вопрос$'), partial_fetch_new_q),
                MessageHandler(Filters.regex('^Сдаться$'), partial_give_up)],
        ANSWER: [MessageHandler(Filters.regex('^Сдаться$'), partial_give_up),
                 MessageHandler(Filters.regex('^Новый вопрос$'), reply_to_bad_new_q),
                 MessageHandler(Filters.text, partial_analyze_answer)]

    },
    fallbacks=[CommandHandler('end', end_this_game)]
    )
    dp.add_handler(conv_hand)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
