# api.py

import asyncio
import hashlib
import json

from fastapi import (
    APIRouter,
    HTTPException,
    WebSocket,
    WebSocketDisconnect
)

from fastapi.responses import Response

from renderer import render_tensor
from render_worker import RenderWorker
from state import state



router = APIRouter()


worker = RenderWorker(
    max_cache=128
)


clients = set()



# --------------------------------------------------
# websocket broadcast
# --------------------------------------------------

async def broadcast(message):

    if not clients:
        return


    data = json.dumps(message)


    dead = []


    for ws in list(clients):

        try:

            await ws.send_text(
                data
            )


        except Exception:

            dead.append(ws)



    for ws in dead:

        clients.discard(ws)



# --------------------------------------------------
# state watcher
# --------------------------------------------------

async def state_watcher():

    print(
        "state watcher started"
    )


    while True:


        event = await asyncio.to_thread(
            state.events.get
        )


        print(
            "broadcast",
            event
        )


        await broadcast({

            "type":
                "tensor_update",

            "tensor":
                event["tensor"],

            "version":
                event["version"]

        })





# --------------------------------------------------
# websocket endpoint
# --------------------------------------------------

@router.websocket(
    "/events"
)
async def events(ws: WebSocket):


    await ws.accept()


    clients.add(
        ws
    )


    print(
        "WS client connected",
        len(clients)
    )


    try:

        while True:

            await ws.receive_text()


    except WebSocketDisconnect:

        clients.discard(
            ws
        )


        print(
            "WS client disconnected"
        )



# --------------------------------------------------
# state api
# --------------------------------------------------

@router.get(
    "/state"
)
async def get_state():

    return state.info()



def get_tensor(name):

    tensor = state.get(
        name
    )


    if tensor is None:

        raise HTTPException(

            404,

            f"Tensor {name} not found"

        )


    return tensor




# --------------------------------------------------
# render key
# --------------------------------------------------

def make_key(

        name,

        version,

        mode,

        batch,

        channel,

        axes,

        separate_norm

):


    raw = "|".join(
        map(
            str,
            [
                name,
                version,
                mode,
                batch,
                channel,
                axes,
                separate_norm
            ]
        )
    )


    return hashlib.md5(
        raw.encode()
    ).hexdigest()




# --------------------------------------------------
# image
# --------------------------------------------------

@router.get(
    "/tensor/{name}/image"
)
async def tensor_image(

        name:str,

        mode:str="single_bc",

        batch:int=0,

        channel:int=0,

        axes:str="B,C,H,W",

        separate_norm:bool=False

):


    tensor = get_tensor(
        name
    )


    version = state.get_version(
        name
    )



    key = make_key(

        name,

        version,

        mode,

        batch,

        channel,

        axes,

        separate_norm

    )



    worker.submit(

        key,

        lambda:

        render_tensor(

            tensor,

            mode=mode,

            batch=batch,

            channel=channel,

            axes=axes,

            separate_norm=separate_norm

        )

    )



    start = asyncio.get_running_loop().time()



    while True:


        result = worker.get(
            key
        )



        if result:


            if result["status"]=="done":

                return Response(

                    result["data"],

                    media_type="image/png",

                    headers={

                        "Cache-Control":
                            "no-store"

                    }

                )


            if result["status"]=="error":

                raise HTTPException(

                    500,

                    result["error"]

                )



        if (
            asyncio.get_running_loop().time()
            -
            start
            >
            30
        ):

            raise HTTPException(

                504,

                "render timeout"

            )



        await asyncio.sleep(
            0.01
        )


