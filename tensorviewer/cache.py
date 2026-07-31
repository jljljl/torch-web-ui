# cache.py

from collections import OrderedDict
import threading
import time


class ImageCache:

    def __init__(
            self,
            max_items=64
    ):

        self.max_items = max_items

        self.data = OrderedDict()

        self.lock = threading.Lock()



    def get(self, key):

        with self.lock:

            if key not in self.data:
                return None


            item = self.data.pop(
                key
            )


            # обновляем порядок LRU
            self.data[key] = item


            return item["data"]



    def put(
            self,
            key,
            value
    ):

        with self.lock:

            if key in self.data:

                self.data.pop(
                    key
                )


            self.data[key] = {

                "data": value,

                "time":
                    time.time()

            }


            while len(self.data) > self.max_items:

                self.data.popitem(
                    last=False
                )



    def has(
            self,
            key
    ):

        with self.lock:

            return key in self.data



    def clear(self):

        with self.lock:

            self.data.clear()



    def size(self):

        with self.lock:

            return len(
                self.data
            )



    def stats(self):

        with self.lock:

            return {

                "items":
                    len(self.data),

                "max":
                    self.max_items

            }