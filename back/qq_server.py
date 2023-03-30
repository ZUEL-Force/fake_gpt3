from pathlib import Path

from random import randint
import requests
import re

from config import QQ_PRITE_URL, QQ_BAN_URL, QQ_GROUP_URL, SERVE_QQ, SERVE_QQ_CODE
from mybasic import db
from myTools import *
from tables import QQ_temp
from private import REMOTE_URL, MY_QQ_ID


def check_key(msg: str):
    for it in SERVE_QQ:
        if it in msg:
            return SERVE_QQ_CODE[it]
    return 0


def do_talk(js: dict, group_id: int):
    my_time = get_time()
    user_id = int(js['user_id'])
    sys_msg = {"role": "system", "content": "你是一个聊天机器人，名字是Raiden，负责和用户沟通。"}
    message = js['message']

    all_pre = QQ_temp.query.filter(QQ_temp.tstamp.__ge__(int(my_time) -
                                                         200)).all()
    my_chat = [sys_msg]
    for it in all_pre:
        if it.from_id == MY_QQ_ID:
            if it.to_id == user_id:
                if it.group_id == group_id:
                    my_chat.append({"role": "assistant", "content": it.text})
        if it.to_id == MY_QQ_ID:
            if it.from_id == user_id:
                if it.group_id == group_id:
                    my_chat.append({"role": "user", "content": it.text})
    my_chat.append({"role": "user", "content": message})

    to_chat = {
        "from": user_id,
        "time": get_time(),
        "messages": my_chat,
        "id": 2,
        "token": "xue_JesAbMQxYQoq"
    }
    ans = requests.post(url=REMOTE_URL, json=to_chat).json()
    if ans['state'] == 0:
        return ans['msg']['answer']
    return '响应超时，请稍后重试。'


def do_help(js: dict):
    return "胖熊还没写help，以后再说"


def do_ban(js: dict):
    message = js['message']
    ban_list = re.findall(r"禁言\[CQ:at,qq=\d+\]", message)

    if len(ban_list) != 1 or str(MY_QQ_ID) in ban_list[0]:
        return "格式错误，应为'@机器人 禁言@禁言对象'"

    ban_id = re.findall(r"\d+", ban_list[0])[0]
    ban_send = {
        "group_id": js['group_id'],
        "user_id": ban_id,
        "duration": 60,
    }
    requests.post(url=QQ_BAN_URL, json=ban_send)
    return "好的，已禁言[CQ:at,qq=%s]" % ban_id


def do_pic(js: dict):
    message = js['message']

    rand_i = randint(-5, 13)
    if "杰哥" in message:
        rand_i = 9
        img_url = rf'E:\githubLib\zuel_force\fakegpt\back\static\img\{rand_i}.png'
    img_url = rf'E:\githubLib\zuel_force\fakegpt\back\static\img\{rand_i}.png'
    if not Path.exists(Path(img_url)):
        img_url = rf'E:\githubLib\zuel_force\fakegpt\back\static\img\{rand_i}.jpg'
    img_url = Path.as_uri(Path(img_url))
    return ("[CQ:image,file=%s]" % img_url)


def get_ans(js: dict, gid: int):
    scode = check_key(js['message'])
    if scode == 0:
        ans = do_talk(js, gid)
    elif scode == 1:
        ans = do_help(js)
    elif scode == 2:
        if gid == -1:
            ans = "该功能需要在群聊中使用。"
        else:
            ans = do_ban(js)
    elif scode == 3:
        ans = do_pic(js)
    return ans


def do_private(js: dict):
    user_id = int(js['user_id'])
    message = js['message']
    my_time = get_time()
    ans = get_ans(js, -1)
    if ans == None:
        return

    qq_msg = QQ_temp(user_id, MY_QQ_ID, my_time, message, -1)
    qq_ans = QQ_temp(MY_QQ_ID, user_id, my_time, ans, -1)

    with app.app_context():
        db.session.add(qq_msg)
        db.session.add(qq_ans)
        db.session.commit()

    qq_send = {"user_id": user_id, "message": ans}
    requests.post(url=QQ_PRITE_URL, json=qq_send)


def do_group(js: dict):
    message = js['message']
    if str(MY_QQ_ID) not in message:
        return

    message = message.replace(f'[CQ:at,qq={MY_QQ_ID}]', '').strip()
    group_id = int(js['group_id'])
    user_id = int(js['user_id'])
    ans = get_ans(js, group_id)
    my_time = get_time()

    qq_msg = QQ_temp(user_id, MY_QQ_ID, my_time, message, group_id)
    qq_ans = QQ_temp(MY_QQ_ID, user_id, my_time, ans, group_id)

    with app.app_context():
        db.session.add(qq_msg)
        db.session.add(qq_ans)
        db.session.commit()

    qq_send = {"group_id": group_id, "message": ans}
    requests.post(url=QQ_GROUP_URL, json=qq_send)


def do_else(js: dict):
    post_type = js['post_type']
    pass
