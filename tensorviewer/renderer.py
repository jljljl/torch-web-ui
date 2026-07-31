import io

import torch
import numpy as np

from PIL import Image



def normalize_image(x):

    x = x.detach().float().cpu()


    x_min = x.min()

    x_max = x.max()


    if x_max - x_min < 1e-8:

        x = torch.zeros_like(x)

    else:

        x = (
            x - x_min
        ) / (
            x_max - x_min
        )


    x = (
        x * 255
    ).clamp(
        0,
        255
    )


    return x.byte()




def to_2d(tensor):

    """
    Преобразует любой tensor в 2D.
    Последние две размерности считаются изображением.
    """

    if not isinstance(
        tensor,
        torch.Tensor
    ):

        raise TypeError(
            "expected torch.Tensor"
        )


    x = tensor


    while x.ndim > 2:

        x = x[0]


    if x.ndim == 0:

        x = x.reshape(
            1,
            1
        )


    elif x.ndim == 1:

        x = x.unsqueeze(
            0
        )


    return x




def render_tensor(tensor):


    x = to_2d(
        tensor
    )


    x = normalize_image(
        x
    )


    img = Image.fromarray(
        x.numpy(),
        mode="L"
    )


    buffer = io.BytesIO()


    img.save(
        buffer,
        format="PNG"
    )


    return buffer.getvalue()