import threading
import torch
from queue import Queue


class TensorState:

    def __init__(self):

        self.tensors = {}

        self.versions = {}

        self.lock = threading.Lock()

        self.events = Queue()



    def update(self, name, tensor):

        with self.lock:

            self.tensors[name] = (
                tensor
                .detach()
                .cpu()
                .clone()
            )


            self.versions[name] = (
                self.versions.get(name,0)
                + 1
            )


            version = self.versions[name]


        # событие вне lock
        self.events.put(
            {
                "tensor": name,
                "version": version
            }
        )



    def get(self,name):

        with self.lock:

            return self.tensors.get(name)



    def get_version(self,name):

        with self.lock:

            return self.versions.get(name,0)



    def info(self):

        with self.lock:

            return {

                name:{
                    "shape":list(t.shape),
                    "dtype":str(t.dtype),
                    "version":self.versions[name]
                }

                for name,t in self.tensors.items()

            }


state = TensorState()