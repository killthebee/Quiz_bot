import os
import random
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
import fetch_quiz_content
import redis

def adjust_score(u_id, adj, r):

    score_key = 'Score_%s'%(u_id)
    current_score = r.get(score_key)
    if current_score is not None:
        new_score = int(current_score) + adj
        r.set(score_key, new_score)
    else:
        r.set(score_key, adj)


def start_game(event, vk_api):

    keyboard = VkKeyboard(one_time=True)

    keyboard.add_button('Начать игру!', color=VkKeyboardColor.DEFAULT)

    keyboard.add_line()
    keyboard.add_button('Мой счёт', color=VkKeyboardColor.DEFAULT)


    vk_api.messages.send(
        peer_id=event.user_id,
        message='Давай поиграем?',
        keyboard=keyboard.get_keyboard(),
        random_id=get_random_id()
    )

def finish_game(event, vk_api):

    text = (
        'Чтобы закончить игру ответьте на вопрос или нажмите cдаться, ' +
        'Затем напишите что-нибудь мне'
    )

    vk_api.messages.send(
        user_id=event.user_id,
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
        peer_id=event.user_id,
        message='Выбирай',
        keyboard=keyboard.get_keyboard(),
        random_id=get_random_id()
    )


def fetch_score(event, vk_api, r):

    users_score_key = 'Score_%s'%(event.user_id)
    users_score = r.get(users_score_key)
    if users_score is None:
        vk_api.messages.send(
            user_id=event.user_id,
            message='В данный момент у вас 0 очков',
            random_id=get_random_id()
        )
    else:
        text = 'В данный момент у вас %s очков'%(users_score)
        vk_api.messages.send(
            user_id=event.user_id,
            message=text,
            random_id=get_random_id()
        )


def analize_text(event, vk_api, q_a_pairs, r):

    user_id = event.user_id
    current_question = r.get(user_id)

    if current_question is None:
        start_game(event, vk_api)
    else:
        right_answer = q_a_pairs[current_question]
        users_answer = event.text
        if users_answer in right_answer:
            resulting_text = 'И это ... ПРАВИЛЬНЫЙ ОТВЕТ!!!'
            score_adjustment = 10
        else:
            resulting_text = 'И это ... ПРОВАЛ БРАЧО!!!'
            score_adjustment = -10
        r.delete(user_id)
        vk_api.messages.send(
            user_id=event.user_id,
            message=resulting_text,
            random_id=get_random_id()
        )
        adjust_score(user_id, score_adjustment, r)

def give_up(q_a_pairs, event, vk_api, r):

    user_id = event.user_id
    current_question = r.get(user_id)

    if current_question is None:
        vk_api.messages.send(
            user_id=event.user_id,
            message='Но у вас нет неотвеченных вопросов!',
            random_id=get_random_id()
        )
    else:
        right_answer = q_a_pairs[current_question]
        sad_text = 'Очень жаль, правильным ответом был: %s'%(right_answer)
        r.delete(user_id)
        vk_api.messages.send(
            user_id=event.user_id,
            message=sad_text,
            random_id=get_random_id()
        )
        adjust_score(user_id, -5, r)



def new_q(q_a_pairs, event, vk_api, r):

    user_id = event.user_id
    if r.get(user_id) is not None:
        vk_api.messages.send(
            user_id=event.user_id,
            message='но у вас уже есть вопрос!',
            random_id=get_random_id()
        )
    else:
        q, a = random.choice(list(q_a_pairs.items()))
        vk_api.messages.send(
            user_id=event.user_id,
            message=q,
            random_id=get_random_id()
        )
        r.set(str(object=user_id),q)



if __name__ == "__main__":

    q_a_pairs = fetch_quiz_content.main()
    r = redis.Redis(
    host=os.environ.get['REDIS_HOST'],
    port=os.environ.get['REDIS_PORT'],
    db=0,
    password=os.environ.get['REDIS_PASWORD'],
    decode_responses=True
    )

    vk_token = os.environ.get['VK_TOKEN']
    vk_session = vk_api.VkApi(token="cd49b2635fff922767f6ab5ab77886ac7dbc6d6a4d43acf94f0f267feca2073572816fad777722027afa6")
    vk_api = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            if event.text == "Сдаться":
                give_up(q_a_pairs, event, vk_api, r)
            elif event.text == "Новый вопрос":
                new_q(q_a_pairs, event, vk_api, r)
            elif event.text == "Мой счёт":
                fetch_score(event, vk_api, r)
            elif event.text == "Начать игру!":
                launch(event, vk_api)
            elif event.text == "Закончить игру":
                finish_game(event, vk_api)
            else:
                analize_text(event, vk_api, q_a_pairs, r)
