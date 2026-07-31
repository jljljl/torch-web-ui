import threading



class ParameterStore:


    def __init__(self):

        self.data = {}

        self.lock = threading.RLock()



    # ---------------------------------------------
    # register
    # ---------------------------------------------

    def register(
            self,
            name,
            dtype,
            value=None
    ):


        with self.lock:


            if value is None:


                if dtype == "int":

                    value = 0


                elif dtype == "float":

                    value = 0.0


                elif dtype == "bool":

                    value = False


                elif dtype == "string":

                    value = ""


                else:

                    value = None



            self.data[name] = {

                "type": dtype,

                "value": value

            }




    # ---------------------------------------------
    # get
    # ---------------------------------------------

    def get(
            self,
            name
    ):


        with self.lock:

            return self.data[name]["value"]




    # ---------------------------------------------
    # set
    # ---------------------------------------------

    def set(
            self,
            name,
            value
    ):


        with self.lock:


            if name not in self.data:

                raise KeyError(
                    name
                )


            dtype = self.data[name]["type"]



            if dtype == "int":

                value = int(value)


            elif dtype == "float":

                value = float(value)


            elif dtype == "bool":

                if isinstance(
                    value,
                    str
                ):

                    value = (
                        value.lower()
                        in
                        (
                            "1",
                            "true",
                            "yes"
                        )
                    )


                else:

                    value = bool(value)



            elif dtype == "string":

                value = str(value)



            self.data[name]["value"] = value




    # ---------------------------------------------
    # json
    # ---------------------------------------------

    def get_dict(self):


        with self.lock:

            return {

                name: {

                    "type": item["type"],

                    "value": item["value"]

                }

                for name, item
                in self.data.items()

            }




    def __getitem__(
            self,
            name
    ):

        return self.get(name)



    def __setitem__(
            self,
            name,
            value
    ):

        self.set(
            name,
            value
        )





params = ParameterStore()