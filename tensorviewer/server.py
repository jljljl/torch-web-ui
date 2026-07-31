import asyncio
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from tensorviewer.api import (
    router,
    state_watcher
)


PACKAGE_DIR = Path(__file__).resolve().parent
STATIC_DIR = PACKAGE_DIR / "static"


if not STATIC_DIR.exists():
    raise RuntimeError(
        f"Missing package static directory: {STATIC_DIR}"
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
        directory=STATIC_DIR,
        html=True
    ),
    name="static"
)



# --------------------------------------------------
# background tasks
# --------------------------------------------------

watcher_task = None



@app.on_event("startup")
async def startup():

    global watcher_task


    watcher_task = asyncio.create_task(
        state_watcher()
    )


    print(
        "server started"
    )



@app.on_event("shutdown")
async def shutdown():

    global watcher_task


    if watcher_task:

        watcher_task.cancel()

        try:
            await watcher_task

        except asyncio.CancelledError:
            pass


    print(
        "server stopped"
    )