import asyncio
import threading

from queue import Queue, Empty

import torch

from tensorviewer.state import state
from tensorviewer.params import params


class TensorViewer:


    def __init__(
            self,
            verbose=False
    ):

        self.verbose = verbose


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




    def set_loop(
            self,
            loop
    ):

        self.loop = loop




    def set_event_callback(
            self,
            callback
    ):

        self.event_callback = callback




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

                n: all_params[n]

                for n in names

                if n in all_params

            }



        if self.verbose:

            print(
                "PARAM UPDATE",
                data
            )




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


                if self.verbose:


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





                if self.event_callback and self.loop:


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


        self.running = False