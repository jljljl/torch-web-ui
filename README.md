````markdown
# TorchWebUI

Web interface for PyTorch model debugging, tensor visualization and experiment control.

TorchWebUI helps you inspect what happens inside neural networks while they are running:

- input batches;
- intermediate activations;
- layer weights;
- feature maps;
- model outputs.

The goal is to provide a lightweight local browser interface for debugging deep learning models.

---

# Features

## Tensor visualization

View PyTorch tensors directly in a browser:

- input images;
- convolution outputs;
- weights;
- activations;
- arbitrary tensors.

Supported:

- automatic tensor shape detection;
- batch/channel navigation;
- tensor grids;
- normalization modes;
- live updates while the model is running.

Example:

```python
viewer.update(
    "input",
    batch
)

viewer.update(
    "layer1_weights",
    model.conv1.weight
)
````

---

# Installation

Install from PyPI:

```bash
pip install torch-web-ui
```

For PyTorch support:

```bash
pip install torch-web-ui[torch]
```

Or install PyTorch separately:

```bash
pip install torch
```

---

# Quick start

```python
from torch_web_ui import TensorViewer


viewer = TensorViewer()


viewer.update(
    "input",
    tensor
)


viewer.run()
```

Open:

```
http://127.0.0.1:8000
```

---

# MNIST live visualization example

This example demonstrates live visualization of:

* input images;
* intermediate convolution output;
* model output;
* convolution weights.

```python
import threading
import time

import torch
import torch.nn as nn

from torch.utils.data import DataLoader
from torchvision import datasets, transforms

import uvicorn

from torch_web_ui import TensorViewer
from torch_web_ui.server import app



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

        layer1 = x


        x = torch.relu(x)


        x = self.conv2(x)


        return x, layer1



# -------------------------------------------------------
# Viewer
# -------------------------------------------------------

viewer = TensorViewer()



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

            output, layer1 = model(images)


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
                output
            )


            viewer.update(
                "layer1_weights",
                model.conv1.weight
            )


            viewer.update(
                "layer2_weights",
                model.conv2.weight
            )


            print(
                "updated batch",
                images.shape
            )


            time.sleep(1)



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

        reload=False

    )
```

Run:

```bash
python examples/mnist.py
```

Open:

```
http://127.0.0.1:8000
```

The browser will automatically receive updated tensors while the model is running.

---

# Tensor modes

## Single tensor view

Display one tensor slice:

```
B,C,H,W
```

Example:

```
input[0,0,:,:]
```

---

## Batch/channel grid

Display multiple images:

```
Batch x Channel
```

Useful for:

* convolution filters;
* feature maps;
* activation visualization.

Example:

```
layer1_weights

16 x 1 x 3 x 3
```

---

# Architecture

TorchWebUI separates tensor collection, rendering and browser communication.

```
PyTorch model

      |

TensorViewer

      |

Tensor state

      |

FastAPI server

      |

Web browser
```

Updates are delivered using WebSocket events.

Rendering runs separately from the model process to avoid blocking training.

---

# Roadmap

## Tensor tools

* [x] Tensor visualization
* [x] Live updates
* [x] Weight visualization
* [x] Batch/channel navigation
* [x] Web interface

## Training control

Planned:

* parameter editor;
* sliders;
* editable tables;
* runtime configuration.

Example:

```
learning_rate   0.001
momentum        0.9
batch_size      32
```

## Console

Planned commands:

```
set lr 0.0005

freeze layer1

save checkpoint

show gradients
```

## Experiment tools

Planned:

* presets;
* notifications;
* training status;
* model inspection.

---

# Development

Clone:

```bash
git clone https://github.com/YOUR_NAME/torch-web-ui.git

cd torch-web-ui
```

Install:

```bash
pip install -e .[dev]
```

Run tests:

```bash
pytest
```

Build package:

```bash
python -m build
```

---

# Project structure

```
torch-web-ui/

src/
└── torch_web_ui/

    viewer.py
    api.py
    server.py
    renderer.py
    state.py

    static/

        index.html
        app.js
        style.css
```

---

# License

TorchWebUI is free for personal, educational and research use.

Commercial use requires a separate license agreement.

See `LICENSE` for details.

---

# Contributing

Issues, suggestions and improvements are welcome.

For large changes, please open a discussion before submitting a pull request.

---

# Future vision

TorchWebUI aims to become a lightweight interactive control panel for PyTorch experiments:

* visualize tensors;
* monitor models;
* edit parameters;
* control experiments;
* debug training directly from a browser.

```
```
