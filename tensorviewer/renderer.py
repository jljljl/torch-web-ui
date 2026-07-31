# renderer.py

from __future__ import annotations

import io
import math

import numpy as np
import torch

from PIL import Image, ImageDraw
from matplotlib import cm


GRID_GAP = 3
TITLE_HEIGHT = 45


# ----------------------------------------------------
# Axes
# ----------------------------------------------------

def parse_axes(text: str):

    mapping = {
        "B": 0,
        "C": 1,
        "H": 2,
        "W": 3,
    }

    parts = (
        text
        .replace(" ", "")
        .upper()
        .split(",")
    )

    if sorted(parts) != [
        "B",
        "C",
        "H",
        "W"
    ]:
        raise ValueError(
            "Axes must be B,C,H,W"
        )

    return [
        mapping[x]
        for x in parts
    ]



# ----------------------------------------------------
# Normalize
# ----------------------------------------------------

def normalize_viridis(
        img,
        global_max=None
):

    img = img.astype(
        np.float32
    )


    if global_max is None:

        max_abs = np.max(
            np.abs(img)
        )

    else:

        max_abs = global_max



    if max_abs < 1e-8:

        norm = np.zeros_like(
            img
        )

    else:

        norm = img / max_abs

        norm = (
            norm + 1.0
        ) * 0.5



    rgba = cm.viridis(
        norm
    )


    return (
        rgba[:, :, :3] * 255
    ).astype(
        np.uint8
    )



# ----------------------------------------------------
# Resize
# ----------------------------------------------------

def resize_keep_ratio(
        img,
        max_size=256
):

    w,h = img.size


    scale = min(
        max_size / w,
        max_size / h
    )


    return img.resize(
        (
            max(
                1,
                int(w*scale)
            ),
            max(
                1,
                int(h*scale)
            )
        ),
        Image.Resampling.NEAREST
    )



# ----------------------------------------------------
# Extract tensor images
# ----------------------------------------------------

def extract_images(
        tensor,
        mode="single_bc",
        batch=0,
        channel=0,
        axes="B,C,H,W",
        limit=None,
):


    perm = parse_axes(
        axes
    )


    t = (
        tensor
        .detach()
        .cpu()
        .permute(*perm)
    )


    if t.ndim != 4:

        raise ValueError(
            f"Expected 4D tensor, got {t.shape}"
        )


    B,C,H,W = t.shape



    # Автоматический лимит
    if limit is None:

        if H*W <= 64:
            limit = 128
        else:
            limit = 32



    result=[]



    def add(b,c):

        arr = (
            t[b,c]
            .numpy()
        )


        result.append(
            {
                "img": arr,

                "title":
                    f"B{b} C{c}",

                "min":
                    float(arr.min()),

                "max":
                    float(arr.max())
            }
        )



    if mode == "single_bc":

        if (
            batch < B
            and
            channel < C
        ):

            add(
                batch,
                channel
            )



    elif mode == "batch_all_channels":

        if batch < B:

            for c in range(C):

                if len(result)>=limit:
                    break

                add(
                    batch,
                    c
                )



    elif mode == "channel_all_batches":

        if channel < C:

            for b in range(B):

                if len(result)>=limit:
                    break

                add(
                    b,
                    channel
                )



    elif mode == "grid_bc":


        pairs=[]


        for b in range(B):

            for c in range(C):

                pairs.append(
                    (
                        b,
                        c
                    )
                )


        # ограничиваем уже готовые пары
        pairs = pairs[:limit]


        for b,c in pairs:

            add(
                b,
                c
            )


    else:

        raise ValueError(
            mode
        )


    #
    # print(
    #     "render:",
    #     mode,
    #     tuple(t.shape),
    #     "images:",
    #     len(result)
    # )


    return result



# ----------------------------------------------------
# PNG generation
# ----------------------------------------------------

def images_to_png(
        images,
        separate_norm=False,
):


    if not images:

        return pil_to_bytes(
            Image.new(
                "RGB",
                (400,100),
                "black"
            )
        )



    if separate_norm:

        global_max=None

    else:

        global_max=max(
            np.max(
                np.abs(
                    x["img"]
                )
            )
            for x in images
        )



    prepared=[]


    for item in images:

        rgb = normalize_viridis(
            item["img"],
            global_max
        )


        img = Image.fromarray(
            rgb
        )


        img = resize_keep_ratio(
            img
        )


        prepared.append(
            (
                img,
                item
            )
        )



    if len(prepared)==1:

        return pil_to_bytes(
            prepared[0][0]
        )



    n=len(prepared)


    cols=int(
        math.ceil(
            math.sqrt(n)
        )
    )


    rows=int(
        math.ceil(
            n/cols
        )
    )


    cell_w=max(
        x[0].width
        for x in prepared
    )


    cell_h=max(
        x[0].height
        for x in prepared
    )



    canvas=Image.new(
        "RGB",
        (
            cols*cell_w
            +(cols-1)*GRID_GAP,

            rows*(cell_h+TITLE_HEIGHT)
            +(rows-1)*GRID_GAP
        ),
        (20,20,20)
    )


    draw=ImageDraw.Draw(
        canvas
    )



    for i,(img,item) in enumerate(prepared):

        col=i%cols
        row=i//cols


        x=col*(cell_w+GRID_GAP)

        y=row*(cell_h+TITLE_HEIGHT+GRID_GAP)



        canvas.paste(
            img,
            (
                x,
                y+TITLE_HEIGHT
            )
        )


        draw.text(
            (
                x+3,
                y+3
            ),

            (
                f'{item["title"]}\n'
                f'min={item["min"]:.3g}\n'
                f'max={item["max"]:.3g}'
            ),

            fill="white"
        )



    return pil_to_bytes(
        canvas
    )



# ----------------------------------------------------
# Public
# ----------------------------------------------------

def render_tensor(
        tensor,
        **kwargs
):

    separate_norm = kwargs.pop(
        "separate_norm",
        False
    )


    images = extract_images(
        tensor,
        **kwargs
    )


    return images_to_png(
        images,
        separate_norm
    )



def pil_to_bytes(img):

    buf=io.BytesIO()


    img.save(
        buf,
        format="PNG",
        optimize=True
    )


    return buf.getvalue()