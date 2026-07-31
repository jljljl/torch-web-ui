import threading


class ParameterStore:


    def __init__(self):

        self.data = {}

        self.types = {}

        self.lock = threading.Lock()



    def register(
            self,
            name,
            dtype
    ):

        with self.lock:

            self.types[name] = dtype

            if name not in self.data:

                self.data[name] = None



    def __setitem__(
            self,
            name,
            value
    ):

        with self.lock:

            if name not in self.types:

                raise KeyError(
                    f"Parameter '{name}' is not registered"
                )


            dtype = self.types[name]


            value = self.validate(
                value,
                dtype
            )


            self.data[name] = value



    def __getitem__(
            self,
            name
    ):

        with self.lock:

            return self.data[name]



    def validate(
            self,
            value,
            dtype
    ):

        if dtype == "int":

            if isinstance(value, bool):
                raise ValueError(
                    "bool is not int"
                )

            return int(value)



        if dtype == "float":

            return float(value)



        if dtype == "str":

            return str(value)



        raise ValueError(
            f"Unknown parameter type: {dtype}"
        )



    def get_dict(self):

        with self.lock:

            return {

                name: {

                    "type": self.types[name],

                    "value": self.data[name]

                }

                for name in self.types

            }



    def update(
            self,
            name,
            value
    ):

        self[name] = value



# global parameter storage

params = ParameterStore()