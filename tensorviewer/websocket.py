# websocket.py

from __future__ import annotations

import asyncio
import json
from typing import Set

from fastapi import WebSocket, WebSocketDisconnect

from tensorviewer.state import state


class ConnectionManager:
    """
    Управляет подключенными браузерами.
    """

    def __init__(self):
        self.clients: Set[WebSocket] = set()

    async def connect(self, ws: WebSocket):

        await ws.accept()
        self.clients.add(ws)


    def disconnect(self, ws: WebSocket):

        self.clients.discard(ws)


    async def broadcast(self, message: dict):

        if not self.clients:
            return

        data = json.dumps(message)

        dead = []

        for ws in self.clients:

            try:
                await ws.send_text(data)

            except Exception:
                dead.append(ws)


        for ws in dead:
            self.disconnect(ws)



manager = ConnectionManager()



async def websocket_endpoint(
        websocket: WebSocket
):

    await manager.connect(websocket)

    try:

        while True:

            # Браузер может присылать ping
            await websocket.receive_text()


    except WebSocketDisconnect:

        manager.disconnect(websocket)



async def event_loop():

    """
    Фоновый цикл.

    Проверяет новые изменения тензоров
    и отправляет события браузеру.
    """

    while True:

        events = state.pop_events()

        for event in events:

            await manager.broadcast(
                event
            )

        await asyncio.sleep(0.05)