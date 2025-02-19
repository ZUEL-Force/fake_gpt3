import hashlib
import random
import time

import requests
from flask import jsonify
from private import *


def get_salt(margin: int = 64):
    alphabet = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789@$#%_?'
    salt = ''
    length = len(alphabet) - 1
    for i in range(0, margin):
        salt += alphabet[random.randint(0, length)]
    return salt


def get_hash(psw: str, salt: str):
    result = psw + salt
    return hashlib.sha256(result.encode('utf-8')).hexdigest()


def wrong(msg: str = 'false', how: int = 1):
    ans = {"msg": msg, "state": how}
    return jsonify(ans)


def right(msg: str = 'ok'):
    ans = {"msg": msg, "state": 0}
    return jsonify(ans)


def get_time():
    return int(time.time())


def check_key(msg: str):
    for it in SERVE_QQ_CODE.keys():
        if it in msg:
            return SERVE_QQ_CODE[it]
    return 0


def get_que_key(msg: str):
    sys_msg = {"role": "system", "content": SYSTEM_MSG_SEARCH}
    user_que = {"role": "user", "content": msg}
    my_chat = [sys_msg, user_que]
    to_chat = {"messages": my_chat}
    ans = requests.post(url=GPT_URL, json=to_chat).json()
    if ans['state'] == 0:
        text = str(ans['msg']['result'])
        keys = text.split(' ')
        return keys
    return []


def get_weather(city: str):
    param = {'key': WEATHER_KEY, 'location': city}
    try:
        responce = dict(requests.get(WEATHER_URL, params=param).json())
        result = responce['results'][0]
        city_path = result['location']['path']
        city_weather = result['now']['text']
        city_temperature = int(result['now']['temperature'])
        city_order = str(city_path).split(',')
        city_order.reverse()
        city_order.pop()
        my_city = ''
        for it in city_order:
            my_city += it
        ans = f'{my_city} 气温：{city_temperature}℃，天气：{city_weather}'
        return ans, 0
    except:
        return '天气获取失败，请稍后再试', 1


def to_baike(bk_key: str):
    param = {'appid': BAIKE_ID, 'bk_key': bk_key}
    try:
        responce = dict(requests.get(BAIDU_BAIKE, params=param).json())
        text = responce['abstract']
        return text, 0
    except:
        return '百度百科接口超时，请稍后再试。', 1
