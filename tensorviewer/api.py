from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
import asyncio
import json
from io import BytesIO

import numpy as np
from PIL import Image
from tensorviewer.state import state


router = APIRouter()


clients = set()



async def broadcast(msg):

    if not clients:
        return

    dead = []

    data = json.dumps(msg)

    for ws in clients:
        try:
            await ws.send_text(data)

        except:
            dead.append(ws)


    for ws in dead:
        clients.discard(ws)



async def state_watcher():

    while True:

        event = await asyncio.to_thread(
            state.events.get
        )


        await broadcast({

            "type":"tensor_update",

            "tensor":event["tensor"],

            "version":event["version"]

        })



@router.websocket("/events")
async def websocket(ws:WebSocket):

    await ws.accept()

    clients.add(ws)


    try:

        while True:
            await ws.receive_text()


    except WebSocketDisconnect:

        clients.discard(ws)




# -----------------------------
# tensor list
# -----------------------------

@router.get("/tensors")
async def tensors():

    return state.info()



# -----------------------------
# tensor info
# -----------------------------

@router.get("/tensors/{name}/info")
async def tensor_info(name:str):

    t = state.get(name)

    if t is None:

        raise HTTPException(
            404,
            "tensor not found"
        )


    return {

        "name":name,

        "shape":list(t.shape),

        "dtype":str(t.dtype),

        "version":state.get_version(name)

    }



# -----------------------------
# raw tensor
# -----------------------------

@router.get(
    "/tensors/{name}/get/{batch}/{channel}/{order}"
)
async def get_tensor(
        name:str,
        batch:int,
        channel:int,
        order:str
):

    t = state.get(name)


    if t is None:

        raise HTTPException(
            404,
            "tensor not found"
        )


    if len(t.shape)==4:

        # BCHW

        if order.lower()=="bchw":

            img = t[
                batch,
                channel
            ]


        else:

            raise HTTPException(
                400,
                "unsupported order"
            )


    elif len(t.shape)==3:

        img=t[batch]


    elif len(t.shape)==2:

        img=t


    else:

        raise HTTPException(
            400,
            "tensor is not image"
        )


    # отдаём numpy bytes
    data = img.detach().cpu().numpy().astype("float32").tobytes()


    return Response(

        data,

        media_type="application/octet-stream"

    )

# -----------------------------
# tensor image png
# -----------------------------

@router.get(
    "/tensors/{name}/image/{batch}/{channel}"
)
async def tensor_image(
        name: str,
        batch: int,
        channel: int
):

    t = state.get(name)


    if t is None:

        raise HTTPException(
            404,
            "tensor not found"
        )


    # BCHW
    if len(t.shape) == 4:

        if batch >= t.shape[0]:
            raise HTTPException(
                400,
                "batch out of range"
            )


        if channel >= t.shape[1]:
            raise HTTPException(
                400,
                "channel out of range"
            )


        img = t[
            batch,
            channel
        ]


    # CHW
    elif len(t.shape) == 3:

        img = t[channel]


    # HW
    elif len(t.shape) == 2:

        img = t


    else:

        raise HTTPException(
            400,
            "unsupported tensor shape"
        )



    arr = (
        img
        .detach()
        .float()
        .cpu()
        .numpy()
    )


    # нормализация 0-255

    mn = arr.min()
    mx = arr.max()


    if mx > mn:

        arr = (
            (arr - mn)
            /
            (mx - mn)
            *
            255
        )


    else:

        arr[:] = 0



    arr = arr.astype(
        np.uint8
    )


    image = Image.fromarray(
        arr,
        mode="L"
    )


    buffer = BytesIO()


    image.save(
        buffer,
        format="PNG"
    )


    return Response(

        buffer.getvalue(),

        media_type="image/png",

        headers={
            "Cache-Control":
            "no-store"
        }

    )

from fastapi import (
    APIRouter,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    Body
)

from tensorviewer.params import params

# -----------------------------
# params
# -----------------------------

@router.get("/params")
async def get_params():

    return params.get_dict()



@router.post("/params/{name}")
async def set_param(
        name: str,
        value=Body(...)
):

    params[name] = value


    return {

        "ok": True,

        "name": name,

        "value": params[name]

    }