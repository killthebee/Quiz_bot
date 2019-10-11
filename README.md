# Бот Викторина

С этим ботов можно играть в некое подобие Что Где Когда. Например
@peremoga322_bot в телеграме
https://vk.com/club184671969 в вк

### Как установить
Python3 должен быть уже установлен. Затем используйте pip (или pip3, есть конфликт с Python2) для установки зависимостей:
```
pip install -r requirements.txt
```
Необходимо получить токены Вк. [Больше инфы](https://vk.com/dev/bots_docs?f=1.1.%2B%D0%9F%D0%BE%D0%BB%D1%83%D1%87%D0%B5%D0%BD%D0%B8%D0%B5%2B%D0%BA%D0%BB%D1%8E%D1%87%D0%B0%2B%D0%B4%D0%BE%D1%81%D1%82%D1%83%D0%BF%D0%B0). 2 и ТГ [botFather](https://medium.com/shibinco/create-a-telegram-bot-using-botfather-and-get-the-api-token-900ba00e0f39). Так же завести свою облачную БД Redis![Redis](https://redislabs.com/)
### Launch examples
Скачав апп и установив переменную окружение(см. ниже) в коммандной строке запустите:
```
python tg_bot.py
```
чтобы запустить викторину в ТГ. или
```
python vk_bot.py
```
для ВК
### Переменные окружение
```
REDIS_HOST
```
Адрес от БД Redis.
```
REDIS_PORT
```
Порт от БД Redis.
```
REDIS_PASWORD
```
Пароль от БД Redis
```
TG_TOKEN
```
Токен телеграма
```
VK_TOKEN
```
Токен группы ВК
```
GROUP_ID
```
Айди группы в ВК
### Project Goals

Код написан в образовательных целях на онлайн-курсе для веб-разработчиков [dvmn.org](https://dvmn.org/).
