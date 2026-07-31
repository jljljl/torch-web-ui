# server.py

import asyncio

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from api import (
    router,
    state_watcher
)


app = FastAPI(
    title="Tensor Viewer"
)



# --------------------------------------------------
# api
# --------------------------------------------------

app.include_router(
    router
)



# --------------------------------------------------
# static
# --------------------------------------------------

app.mount(

    "/",

    StaticFiles(

        directory="static",

        html=True

    ),

    name="static"

)



# --------------------------------------------------
# background tasks
# --------------------------------------------------

watcher_task = None



@app.on_event(
    "startup"
)
async def startup():


    global watcher_task


    watcher_task = asyncio.create_task(

        state_watcher()

    )


    print(
        "server started"
    )




@app.on_event(
    "shutdown"
)
async def shutdown():


    global watcher_task


    if watcher_task:

        watcher_task.cancel()



    print(
        "server stopped"
    )