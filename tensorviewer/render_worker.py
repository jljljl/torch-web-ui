# render_worker.py

import threading
import queue
import time

from tensorviewer.cache import ImageCache



class RenderWorker:

    def __init__(
            self,
            max_cache=128
    ):

        self.jobs = queue.Queue()

        self.cache = ImageCache(
            max_items=max_cache
        )


        # key -> state
        #
        # {
        #   "status":
        #       queued/running/done/error,
        #
        #   "data":
        #       bytes,
        #
        #   "error":
        #       str
        # }

        self.tasks = {}

        self.lock = threading.Lock()



        self.thread = threading.Thread(

            target=self._loop,

            daemon=True

        )

        self.thread.start()



    # --------------------------------------------------
    # submit
    # --------------------------------------------------

    def submit(
            self,
            key,
            func
    ):


        # уже есть готовый PNG
        cached = self.cache.get(
            key
        )


        if cached is not None:

            with self.lock:

                self.tasks[key] = {

                    "status":
                        "done",

                    "data":
                        cached

                }


            return key



        with self.lock:


            # уже считается
            if key in self.tasks:

                return key



            self.tasks[key] = {

                "status":
                    "queued",

                "data":
                    None

            }



        self.jobs.put(
            (
                key,
                func
            )
        )


        return key



    # --------------------------------------------------
    # get status
    # --------------------------------------------------

    def get(
            self,
            key
    ):

        with self.lock:

            return self.tasks.get(
                key
            )



    # --------------------------------------------------
    # worker thread
    # --------------------------------------------------

    def _loop(self):

        while True:


            key,func = (
                self.jobs.get()
            )



            with self.lock:

                if key in self.tasks:

                    self.tasks[key]["status"] = \
                        "running"



            try:


                start = time.time()


                data = func()



                elapsed = (
                    time.time()
                    -
                    start
                )


                print(
                    f"[render] {key} "
                    f"{elapsed:.3f}s"
                )



                self.cache.put(
                    key,
                    data
                )



                with self.lock:

                    self.tasks[key] = {

                        "status":
                            "done",

                        "data":
                            data

                    }



            except Exception as e:


                print(
                    "[render error]",
                    e
                )


                with self.lock:

                    self.tasks[key] = {

                        "status":
                            "error",

                        "error":
                            str(e)

                    }



            finally:


                self.jobs.task_done()



                # чистим старые состояния
                self._cleanup()



    # --------------------------------------------------
    # cleanup
    # --------------------------------------------------

    def _cleanup(
            self,
            age=60
    ):

        now = time.time()


        with self.lock:

            remove=[]


            for key,item in self.tasks.items():

                if item["status"] in (
                    "done",
                    "error"
                ):

                    item_time = (
                        item.get(
                            "time",
                            now
                        )
                    )


                    if now-item_time > age:

                        remove.append(
                            key
                        )



            for key in remove:

                self.tasks.pop(
                    key,
                    None
                )



    # --------------------------------------------------
    # stats
    # --------------------------------------------------

    def stats(self):

        with self.lock:

            return {

                "queue":
                    self.jobs.qsize(),

                "tasks":
                    len(self.tasks),

                "cache":
                    self.cache.size()

            }