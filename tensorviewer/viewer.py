# viewer.py

import asyncio
import threading
from queue import Queue, Empty

import torch

from state import state


class TensorViewer:


    def __init__(self):

        self.queue = Queue()

        self.running = True

        self.event_callback = None

        self.loop = None


        self.thread = threading.Thread(
            target=self._worker,
            daemon=True
        )

        self.thread.start()



    def set_loop(self, loop):

        self.loop = loop



    def set_event_callback(self, callback):

        self.event_callback = callback



    def update(
            self,
            name,
            tensor
    ):

        if not isinstance(
                tensor,
                torch.Tensor
        ):
            raise ValueError(
                "Expected torch.Tensor"
            )


        self.queue.put(
            (
                name,
                tensor
            )
        )



    def _worker(self):

        while self.running:

            try:

                name, tensor = self.queue.get(
                    timeout=0.2
                )


            except Empty:

                continue


            try:

                state.update(
                    name,
                    tensor
                )


                version = state.get_version(
                    name
                )


                print(
                    "updated",
                    name,
                    tensor.shape,
                    "v=",
                    version
                )


                if self.event_callback:


                    if self.loop:


                        asyncio.run_coroutine_threadsafe(

                            self.event_callback(
                                name
                            ),

                            self.loop

                        )


            except Exception as e:

                print(
                    "[viewer]",
                    e
                )


            finally:

                self.queue.task_done()



    def stop(self):

        self.running=False