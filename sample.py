# -*- coding: utf-8 -*-
import asyncio
import http.cookies
import random
from typing import *

import aiohttp
import websockets
import json
import blivedm
import blivedm.models.web as web_models

# 直播间ID的取值看直播间URL
TEST_ROOM_IDS = [
    30622172
]

# 这里填一个已登录账号的cookie的SESSDATA字段的值。不填也可以连接，但是收到弹幕的用户名会打码，UID会变成0
SESSDATA = ''

session: Optional[aiohttp.ClientSession] = None
websocket_clients: Set[websockets.WebSocketServerProtocol] = set()


async def main():
    init_session()
    ws_server = websockets.serve(handle_websocket, 'localhost', 8888)
    try:
        await asyncio.gather(
            run_single_client(),
            run_multi_clients(),
            ws_server
        )
    finally:
        await session.close()


def init_session():
    cookies = http.cookies.SimpleCookie()
    cookies['SESSDATA'] = SESSDATA
    cookies['SESSDATA']['domain'] = 'bilibili.com'

    global session
    session = aiohttp.ClientSession()
    session.cookie_jar.update_cookies(cookies)

async def handle_websocket(websocket, path):
    global websocket_clients
    websocket_clients.add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        websocket_clients.remove(websocket)

async def broadcast_message(message: str):
    websockets_to_remove = set()
    for websocket in websocket_clients:
        try:
            await websocket.send(message)
        except:
            websockets_to_remove.add(websocket)
    for websocket in websockets_to_remove:
        websocket_clients.remove(websocket)

async def run_single_client():
    """
    演示监听一个直播间
    """
    room_id = random.choice(TEST_ROOM_IDS)
    client = blivedm.BLiveClient(room_id, session=session)
    handler = MyHandler()
    client.set_handler(handler)

    client.start()
    try:
        # 演示5秒后停止
        await asyncio.sleep(5)
        client.stop()

        await client.join()
    finally:
        await client.stop_and_close()


async def run_multi_clients():
    """
    演示同时监听多个直播间
    """
    clients = [blivedm.BLiveClient(room_id, session=session) for room_id in TEST_ROOM_IDS]
    handler = MyHandler()
    for client in clients:
        client.set_handler(handler)
        client.start()

    try:
        await asyncio.gather(*(
            client.join() for client in clients
        ))
    finally:
        await asyncio.gather(*(
            client.stop_and_close() for client in clients
        ))


class MyHandler(blivedm.BaseHandler):
    # 演示如何添加自定义回调
    _CMD_CALLBACK_DICT = blivedm.BaseHandler._CMD_CALLBACK_DICT.copy()
    
    # 入场消息回调
    async def __interact_word_callback_async(self, client: blivedm.BLiveClient, command: dict):
        message = f"[{client.room_id}] INTERACT_WORD: uname={command['data']['uname']}"
        print(message)
        await broadcast_message(json.dumps({
            "Type": 3,
            "Data": {
                "User": {
                    "Nickname": command['data']['uname']
                }}}))

    def __interact_word_callback(self, client: blivedm.BLiveClient, command: dict):
        asyncio.create_task(self.__interact_word_callback_async(client, command))
    
    _CMD_CALLBACK_DICT['INTERACT_WORD'] = __interact_word_callback  # noqa

    def _on_heartbeat(self, client: blivedm.BLiveClient, message: web_models.HeartbeatMessage):
        print(f'[{client.room_id}] 心跳')

    async def _on_danmaku_async(self, client: blivedm.BLiveClient, message: web_models.DanmakuMessage):
        print(f'[{client.room_id}] {message.uname}：{message.msg}')
        await broadcast_message(json.dumps({
            "Type": 1,
            "Data": {
                "User": {
                    "Nickname": message.uname
                },
                "Content": message.msg
            }
        }))

    def _on_danmaku(self, client: blivedm.BLiveClient, message: web_models.DanmakuMessage):
        asyncio.create_task(self._on_danmaku_async(client, message))


    async def _on_gift_async(self, client: blivedm.BLiveClient, message: web_models.GiftMessage):
        message_text = f'[{client.room_id}] {message.uname} 赠送{message.gift_name}x{message.num}' \
                       f' （{message.coin_type}瓜子x{message.total_coin}）'
        print(message_text)
        await broadcast_message(json.dumps({
            "Type": 5,
            "Data": {
                "User": {
                    "Nickname": message.uname
                },
                "GiftName": message.gift_name,
                "GiftCount": message.num
        }}))

    def _on_gift(self, client: blivedm.BLiveClient, message: web_models.GiftMessage):
        asyncio.create_task(self._on_gift_async(client, message))

    async def _on_buy_guard_async(self, client: blivedm.BLiveClient, message: web_models.GuardBuyMessage):
        message_text = f'[{client.room_id}] {message.username} 购买{message.gift_name}'
        print(message_text)
        await broadcast_message(json.dumps({
            "Type": 5,
            "Data": {
                "User": {
                    "Nickname": message.username
                },
                "GiftName": message.gift_name,
                "GiftCount": message.num
        }}))

    def _on_buy_guard(self, client: blivedm.BLiveClient, message: web_models.GuardBuyMessage):
        asyncio.create_task(self._on_buy_guard_async(client, message))

    def _on_super_chat(self, client: blivedm.BLiveClient, message: web_models.SuperChatMessage):
        print(f'[{client.room_id}] 醒目留言 ¥{message.price} {message.uname}：{message.message}')


if __name__ == '__main__':
    asyncio.run(main())