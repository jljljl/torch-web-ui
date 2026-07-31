import asyncio
import threading
from queue import Queue, Empty

import torch

from tensorviewer.state import state
from tensorviewer.params import params



class TensorViewer:


    def __init__(self):

        self.params = params

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



    # --------------------------------------------------
    # parameters
    # --------------------------------------------------

    def register_parameter(
            self,
            name,
            dtype
    ):

        self.params.register(
            name,
            dtype
        )



    def update_params(
            self,
            names=None
    ):

        if names is None:

            data = self.params.get_dict()

        else:

            all_params = self.params.get_dict()

            data = {
                name: all_params[name]
                for name in names
                if name in all_params
            }


        print(
            "PARAM UPDATE",
            data
        )



    # --------------------------------------------------
    # tensor update
    # --------------------------------------------------

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



    # --------------------------------------------------
    # worker
    # --------------------------------------------------

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



                if (
                    self.event_callback
                    and
                    self.loop
                ):

                    asyncio.run_coroutine_threadsafe(

                        self.event_callback(
                            name,
                            version
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



    # --------------------------------------------------
    # stop
    # --------------------------------------------------

    def stop(self):

        self.running = False