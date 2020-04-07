import os
import requests
from flask import Flask, request
import logging
import json

app = Flask(__name__)
TOKEN = "Njk0NDcxMTUyMTg1MTE0NjI0.XoMHAA.NSwRs6ZXy3dKk8Uu--EhyHJvV58"
URL = "https://translate.yandex.net/api/v1.5/tr.json/translate"
KEY = "trnsl.1.1.20200330T194901Z.c645c08a6c640f8c.29741f50bd6d553614ecc9705ac6efbf3e6e5fff"

logging.basicConfig(level=logging.INFO, filename='app.log', format='%(asctime)s %(levelname)s %(name)s %(message)s')


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

    logging.info('Request: %r', response)

    return json.dumps(response)


def handle_dialog(res, req):
    user_id = req['session']['user_id']

    if req['session']['new']:
        res['response']['text'] = 'Привет! Я могу перевести слово на английский. ' \
                                  'Для этого скажи: Переведи слово и само слово'
        return

    res['response']['text'] = get_translate_word(req)


def get_translate_word(req):
    words = []
    for word in req['request']['nlu']['tokens'][2:]:
        words.append(word)
    params = {
        "key": KEY,
        "text": " ".join(words),
        "lang": "ru-en"
    }
    response = requests.get(URL, params=params)
    return response.json()['text'][0]


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
