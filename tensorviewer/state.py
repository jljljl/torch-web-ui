import threading

from queue import Queue

import torch



class TensorState:


    def __init__(self):

        self.tensors = {}

        self.versions = {}

        self.events = Queue()


        self.lock = threading.RLock()



    # ---------------------------------------------
    # update
    # ---------------------------------------------

    def update(
            self,
            name,
            tensor
    ):


        if not isinstance(
            tensor,
            torch.Tensor
        ):

            raise TypeError(
                "expected torch.Tensor"
            )



        with self.lock:


            self.tensors[name] = tensor.detach()


            version = (
                self.versions.get(
                    name,
                    0
                )
                +
                1
            )


            self.versions[name] = version



        self.events.put({

            "tensor": name,

            "version": version

        })




    # ---------------------------------------------
    # get
    # ---------------------------------------------

    def get(
            self,
            name
    ):


        with self.lock:

            return self.tensors.get(
                name
            )




    # ---------------------------------------------
    # version
    # ---------------------------------------------

    def get_version(
            self,
            name
    ):


        with self.lock:

            return self.versions.get(
                name,
                0
            )




    # ---------------------------------------------
    # info
    # ---------------------------------------------

    def info(self):


        result = {}


        with self.lock:


            for name, tensor in self.tensors.items():


                result[name] = {

                    "shape":
                        list(
                            tensor.shape
                        ),

                    "dtype":
                        str(
                            tensor.dtype
                        ),

                    "version":
                        self.versions.get(
                            name,
                            0
                        )

                }



        return result




state = TensorState()