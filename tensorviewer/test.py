import threading
import time

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

import uvicorn

from tensorviewer.viewer import TensorViewer
from tensorviewer.server import app


# -------------------------------------------------------
# Simple CNN
# -------------------------------------------------------

class Net(nn.Module):

    def __init__(self):
        super().__init__()

        self.conv1 = nn.Conv2d(
            1,
            16,
            3,
            padding=1
        )

        self.conv2 = nn.Conv2d(
            16,
            32,
            3,
            padding=1
        )

    def forward(self, x):

        x = self.conv1(x)

        out1 = x

        x = torch.relu(x)

        x = self.conv2(x)

        return x, out1


# -------------------------------------------------------
# Viewer
# -------------------------------------------------------

viewer = TensorViewer()

params = viewer.params
viewer.register_parameter("lr", "float")
viewer.register_parameter("myParam", "str")
params["lr"] = 1e-4
params["myParam"] = "Hello World!"
viewer.update_params()
# -------------------------------------------------------
# Dataset
# -------------------------------------------------------

dataset = datasets.MNIST(

    root="./mnist",

    train=True,

    download=True,

    transform=transforms.ToTensor()

)


loader = DataLoader(

    dataset,

    batch_size=16,

    shuffle=True

)


model = Net()


# -------------------------------------------------------
# Producer
# -------------------------------------------------------

def producer():

    while True:

        for images, _ in loader:

            out, layer1 = model(images)

            viewer.update(
                "input",
                images
            )

            viewer.update(
                "layer1_output",
                layer1
            )

            viewer.update(
                "output",
                out
            )

            viewer.update(
                "layer1_weights",
                model.conv1.weight
            )

            viewer.update(
                "layer2_weights",
                model.conv2.weight
            )
            print("update")
            time.sleep(0.001)



threading.Thread(

    target=producer,

    daemon=True

).start()


# -------------------------------------------------------
# Run server
# -------------------------------------------------------

if __name__ == "__main__":

    uvicorn.run(

        app,

        host="127.0.0.1",

        port=8000,

        reload=False,

        access_log=False,

    )