import asyncio
import hashlib
import json
import time

from fastapi import (
    APIRouter,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    Body
)

from fastapi.responses import Response

from tensorviewer.renderer import render_tensor
from tensorviewer.render_worker import RenderWorker
from tensorviewer.state import state
from tensorviewer.params import params


router = APIRouter()


worker = RenderWorker(
    max_cache=128
)


clients = set()



# --------------------------------------------------
# websocket
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




@router.websocket(
    "/events"
)
async def events(ws: WebSocket):

    await ws.accept()


    clients.add(
        ws
    )


    print(
        "websocket connected",
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
            "websocket disconnected",
            len(clients)
        )





async def state_watcher():

    print(
        "state watcher started"
    )


    pending = {}


    last_send = 0


    interval = 1.0 / 60.0



    while True:


        event = await asyncio.to_thread(
            state.events.get
        )


        pending[
            event["tensor"]
        ] = event["version"]



        now = time.perf_counter()



        if (
            now - last_send
            <
            interval
        ):

            continue



        last_send = now



        updates = pending

        pending = {}



        for name, version in updates.items():


            await broadcast({

                "type":
                    "tensor_update",

                "tensor":
                    name,

                "version":
                    version

            })





# --------------------------------------------------
# state
# --------------------------------------------------

@router.get(
    "/state"
)
async def get_state():

    return state.info()




# --------------------------------------------------
# params
# --------------------------------------------------

@router.get(
    "/params"
)
async def get_params():

    return params.get_dict()




@router.post(
    "/params/{name}"
)
async def set_param(
        name: str,
        value=Body(...)
):

    params[name] = value


    return {

        "ok":
            True,

        "name":
            name,

        "value":
            params[name]

    }





# --------------------------------------------------
# tensor image
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





@router.get(
    "/tensor/{name}/image"
)
async def tensor_image(

        name: str,

        mode: str = "single_bc",

        batch: int = 0,

        channel: int = 0,

        axes: str = "B,C,H,W",

        separate_norm: bool = False

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


            if result["status"] == "done":

                return Response(

                    result["data"],

                    media_type="image/png",

                    headers={
                        "Cache-Control":
                            "no-store"
                    }

                )



            if result["status"] == "error":

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