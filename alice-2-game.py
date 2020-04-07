import os
from flask import Flask, request
import logging
import json
import random
from geo import get_geo_info

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

cities = {
    'москва': ['1540737/daa6e420d33102bf6947', '213044/7df73ae4cc715175059e'],
    'нью-йорк': ['1652229/728d5c86707054d4745f', '1030494/aca7ed7acefde2606bdc'],
    'париж': ["1652229/f77136c2364eb90a3ea8", '123494/aca7ed7acefd12e606bdc']
}

sessionStorage = {}


@app.route('/post', methods=['POST'])
def main():
    logging.info('Request: %r', request.json)
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }
    handle_dialog(response, request.json)
    logging.info('Response: %r', response)
    return json.dumps(response)


def handle_dialog(res, req):
    user_id = req['session']['user_id']
    if req['session']['new']:
        res['response']['text'] = 'Привет! Назови своё имя!'
        sessionStorage[user_id] = {
            'first_name': None,
            'game_started': False,
            'guess_city': False
        }
        return

    if sessionStorage[user_id]['first_name'] is None:
        first_name = get_first_name(req)
        if first_name is None:
            res['response']['text'] = 'Не расслышала имя. Повтори, пожалуйста!'
        else:
            sessionStorage[user_id]['first_name'] = first_name
            sessionStorage[user_id]['guessed_cities'] = []
            res['response']['text'] = f'Приятно познакомиться, {first_name.title()}. Я Алиса. Отгадаешь город по фото?'
            res['response']['buttons'] = [
                {
                    'title': 'Да',
                    'hide': True
                },
                {
                    'title': 'Нет',
                    'hide': True
                },
                {
                    'title': "Помощь",
                    'hide': False
                }
            ]
    else:
        if 'помощь' in req['request']['nlu']['tokens']:
            res['response']['text'] = 'Справка:\n' \
                                      '1. Я присылаю вам фото города\n' \
                                      '2. Вы должны угадать его\n' \
                                      '3. Сказать его мне\n' \
                                      '4. Угадываете - молодец. Нет - я помогу'
            return
        if not sessionStorage[user_id]['game_started']:
            if 'да' in req['request']['nlu']['tokens']:
                if len(sessionStorage[user_id]['guessed_cities']) == 3:
                    res['response']['text'] = f'Ты, {sessionStorage[user_id]["first_name"]}, отгадал все города!'
                    res['end_session'] = True
                else:
                    sessionStorage[user_id]['game_started'] = True
                    sessionStorage[user_id]['attempt'] = 1
                    play_game(res, req)
            elif 'нет' in req['request']['nlu']['tokens']:
                res['response']['text'] = 'Ну и ладно!'
                res['end_session'] = True
            else:
                res['response']['text'] = 'Не поняла ответа! Так да или нет?'
                res['response']['buttons'] = [
                    {
                        'title': 'Да',
                        'hide': True
                    },
                    {
                        'title': 'Нет',
                        'hide': True
                    }
                ]
        else:
            play_game(res, req)


def play_game(res, req):
    user_id = req['session']['user_id']
    attempt = sessionStorage[user_id]['attempt']
    if attempt == 1:
        city = random.choice(list(cities))
        while city in sessionStorage[user_id]['guessed_cities']:
            city = random.choice(list(cities))
        sessionStorage[user_id]['city'] = city
        sessionStorage[user_id]['country'] = get_geo_info("city", "country")
        res['response']['card'] = {}
        res['response']['card']['type'] = 'BigImage'
        res['response']['card']['title'] = 'Что это за город?'
        res['response']['card']['image_id'] = cities[city][attempt - 1]
        res['response']['text'] = 'Тогда сыграем!'
    else:
        if not sessionStorage[user_id]['guess_city']:
            city = sessionStorage[user_id]['city']
            if get_city(req) == city:
                res['response']['text'] = 'Правильно! А в какой стране этот город?'
                sessionStorage[user_id]['game_started'] = True
                sessionStorage[user_id]['guess_city'] = True
                sessionStorage[user_id]['attempt'] = 2
                return
            else:
                if attempt == 3:
                    res['response'][
                        'text'] = f'Вы, {sessionStorage[user_id]["first_name"]}, пытались. Это {city.title()}. ' \
                                  f'Сыграем ещё?'
                    sessionStorage[user_id]['game_started'] = False
                    sessionStorage[user_id]['guess_city'] = False
                    sessionStorage[user_id]['guessed_cities'].append(city)
                    return
                else:
                    res['response']['card'] = {}
                    res['response']['card']['type'] = 'BigImage'
                    res['response']['card'][
                        'title'] = f'Неправильно. Вот тебе, {sessionStorage[user_id]["first_name"]}, ' \
                                   f'дополнительное фото'
                    res['response']['card']['image_id'] = cities[city][attempt - 1]
                    res['response']['text'] = f'А вот и не угадал, {sessionStorage[user_id]["first_name"]}!'
        else:
            country = sessionStorage[user_id]['country']
            if get_country(req) == country:
                res['response']['text'] = 'Правильно! Сыграем ещё раз?'
                sessionStorage[user_id]['guessed_cities'].append(sessionStorage[user_id]['city'])
                sessionStorage[user_id]['game_started'] = False
                sessionStorage[user_id]['guess_city'] = False
                res['response']['buttons'] = [
                    {
                        'title': 'Да',
                        'hide': True
                    },
                    {
                        'title': 'Нет',
                        'hide': True
                    },
                    {
                        'title': 'Покажи город на карте',
                        "url": f"https://yandex.ru/maps/?mode=search&text={sessionStorage[user_id]['city']}",
                        'hide': True
                    }
                ]
            else:
                res['response'][
                    'text'] = f'Вы, {sessionStorage[user_id]["first_name"]}, пытались. Это {country}. Сыграем ещё?'
                sessionStorage[user_id]['game_started'] = False
                sessionStorage[user_id]['guess_city'] = False
                sessionStorage[user_id]['guessed_cities'].append(sessionStorage[user_id]['city'])
                return
    sessionStorage[user_id]['attempt'] += 1


def get_city(req):
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.GEO':
            return entity['value'].get('city', None)


def get_country(req):
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.GEO':
            return entity['value'].get('country', None)


def get_first_name(req):
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.FIO':
            return entity['value'].get('first_name', None)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
