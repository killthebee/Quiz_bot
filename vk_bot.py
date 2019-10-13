import random
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import fetch_quiz_content
import redis_db as rdb
import requests


def start_game(event, vk_api):

    keyboard = VkKeyboard(one_time=True)

    keyboard.add_button('Начать игру!', color=VkKeyboardColor.DEFAULT)

    keyboard.add_line()
    keyboard.add_button('Мой счёт', color=VkKeyboardColor.DEFAULT)
    vk_api.messages.send(
        peer_id=event.obj.peer_id,
        message='Привет',
        keyboard=keyboard.get_keyboard(),
        random_id= get_random_id()
    )

def finish_game(event, vk_api):

    text = (
        'Чтобы закончить игру ответьте на вопрос или нажмите cдаться, ' +
        'Затем напишите что-нибудь мне'
    )

    vk_api.messages.send(
        peer_id=event.obj.peer_id,
        message=text,
        random_id=get_random_id()
    )


def launch(event, vk_api):

    keyboard = VkKeyboard()

    keyboard.add_button('Мой счёт', color=VkKeyboardColor.DEFAULT)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.DEFAULT)

    keyboard.add_line()
    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.DEFAULT)
    keyboard.add_line()
    keyboard.add_button('Закончить игру', color=VkKeyboardColor.DEFAULT)

    vk_api.messages.send(
        peer_id=event.obj.peer_id,
        message='Выбирай',
        keyboard=keyboard.get_keyboard(),
        random_id=get_random_id()
    )


def fetch_score(event, vk_api, r):

    vk_user_id = 'VK_%s'%(event.obj.user_id)
    users_score_key = 'Score_%s'%(vk_user_id)
    users_score = r.get(users_score_key)
    if users_score is None:
        vk_api.messages.send(
            peer_id=event.obj.peer_id,
            message='В данный момент у вас 0 очков',
            random_id=get_random_id()
        )
    else:
        text = 'В данный момент у вас %s очков'%(users_score)
        vk_api.messages.send(
            peer_id=event.obj.peer_id,
            message=text,
            random_id=get_random_id()
        )


def analyze_text(event, vk_api, q_a_pairs, r):

    vk_user_id = 'VK_%s'%(event.obj.user_id)
    score_key = 'Score_%s'%(vk_user_id)
    current_question = r.get(vk_user_id)

    if current_question is None:
        start_game(event, vk_api)
    else:
        right_answer = q_a_pairs[current_question]
        offset = 1
        first_index_of_message = event.obj.text.find(']') + offset
        users_answer = event.obj.text[first_index_of_message:]
        vk_api.messages.send(
            peer_id=event.obj.peer_id,
            message=users_answer,
            random_id=get_random_id()
        )
        vk_api.messages.send(
            peer_id=event.obj.peer_id,
            message=right_answer,
            random_id=get_random_id()
        )
        if users_answer in right_answer:
            resulting_text = 'И это ... ПРАВИЛЬНЫЙ ОТВЕТ!!!'
            score_adjustment = 10
        else:
            resulting_text = 'И это ... ПРОВАЛ БРАЧО!!!'
            score_adjustment = -10
        r.delete(vk_user_id)
        vk_api.messages.send(
            peer_id=event.obj.peer_id,
            message=resulting_text,
            random_id=get_random_id()
        )
        r.incr(score_key, score_adjustment)


def give_up(q_a_pairs, event, vk_api, r):

    vk_user_id = 'VK_%s'%(event.obj.user_id)
    score_key = 'Score_%s'%(vk_user_id)
    current_question = r.get(vk_user_id)

    if current_question is None:
        vk_api.messages.send(
            peer_id=event.obj.peer_id,
            message='Но у вас нет неотвеченных вопросов!',
            random_id=get_random_id()
        )
    else:
        right_answer = q_a_pairs[current_question]
        sad_text = 'Очень жаль, правильным ответом был: %s'%(right_answer)
        r.delete(vk_user_id)
        vk_api.messages.send(
            peer_id=event.obj.peer_id,
            message=sad_text,
            random_id=get_random_id()
        )
        score_adjustment = -5
        r.incr(score_key, score_adjustment)


def fetch_new_q(q_a_pairs, event, vk_api, r):

    vk_user_id = 'VK_%s'%(event.obj.user_id)
    if r.get(vk_user_id) is not None:
        vk_api.messages.send(
            peer_id=event.obj.peer_id,
            message='но у вас уже есть вопрос!',
            random_id=get_random_id()
        )
    else:
        question = random.choice(list(q_a_pairs.keys()))
        vk_api.messages.send(
            peer_id=event.obj.peer_id,
            message=question,
            random_id=get_random_id()
        )
        r.set(vk_user_id, question)


if __name__ == "__main__":

    q_a_pairs = fetch_quiz_content.main()
    r = rdb.connect_to_db()
    vk_token = os.environ.get['VK_TOKEN']
    vk_session = vk_api.VkApi(token=vk_token)
    vk_api = vk_session.get_api()
    vk_group_id = os.environ.get['GROUP_ID']
    while True:
        longpoll = VkBotLongPoll(vk_session, vk_group_id)
        try:
            for event in longpoll.listen():
                offset = 2
                first_index_of_message = event.obj.text.find(']') + offset
                message_text = event.obj.text[first_index_of_message:]
                if message_text == "Сдаться":
                    give_up(q_a_pairs, event, vk_api, r)
                elif message_text == "Новый вопрос":
                    fetch_new_q(q_a_pairs, event, vk_api, r)
                elif message_text == "Мой счёт":
                    fetch_score(event, vk_api, r)
                elif message_text == "Начать игру!":
                    launch(event, vk_api)
                elif message_text == "Закончить игру":
                    finish_game(event, vk_api)
                else:
                    analyze_text(event, vk_api, q_a_pairs, r)

        except requests.exceptions.ReadTimeout as timeout:
            continue
