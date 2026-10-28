# MIT License
#
# Copyright (c) 2026 ARC Prize Foundation
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
from arcengine import (
    ActionInput,
    ARCBaseGame,
    Camera,
    GameAction,
    Level,
    RenderableUserDisplay,
    Sprite,
)

sprites = {
    "adbrqflmwi": Sprite(
        pixels=[
            [8, 8, 8, 4, 8, 8, 8],
        ],
        name="adbrqflmwi",
        visible=True,
        collidable=True,
        tags=["ksmzdcblcz", "syaipsfndp"],
    ),
    "jgfvrvnkaz": Sprite(
        pixels=[
            [8, 8, 8, 8, 8],
        ],
        name="jgfvrvnkaz",
        visible=True,
        collidable=True,
        tags=["ksmzdcblcz", "sys_click"],
    ),
    "mdhkebfsmg": Sprite(
        pixels=[
            [8],
            [8],
            [8],
            [8],
        ],
        name="mdhkebfsmg",
        visible=True,
        collidable=True,
        tags=["ksmzdcblcz", "sys_click"],
    ),
    "nadtnzkesz": Sprite(
        pixels=[
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        ],
        name="nadtnzkesz",
        visible=True,
        collidable=True,
    ),
    "nkrtlkykwe": Sprite(
        pixels=[
            [6],
        ],
        name="nkrtlkykwe",
        visible=True,
        collidable=True,
        tags=["nkrtlkykwe"],
    ),
    "nvzozwqarf": Sprite(
        pixels=[
            [8, 8, 8, 8, 8, 8, 8, 8],
        ],
        name="nvzozwqarf",
        visible=True,
        collidable=True,
        tags=["ksmzdcblcz", "sys_click"],
    ),
    "odioorqnkn": Sprite(
        pixels=[
            [8, 8, 8, 8, 8, 8],
        ],
        name="odioorqnkn",
        visible=True,
        collidable=True,
        tags=["ksmzdcblcz", "sys_click"],
    ),
    "qwsmjdrvqj": Sprite(
        pixels=[
            [15, -1],
            [15, 15],
        ],
        name="qwsmjdrvqj",
        visible=True,
        collidable=True,
        tags=["hfjpeygkxy", "sys_click"],
    ),
    "syaipsfndp": Sprite(
        pixels=[
            [4],
        ],
        name="syaipsfndp",
        visible=True,
        collidable=True,
        tags=["syaipsfndp"],
    ),
    "trurgcakbj": Sprite(
        pixels=[
            [8, 8, 8, 8],
        ],
        name="trurgcakbj",
        visible=True,
        collidable=True,
        tags=["ksmzdcblcz", "sys_click"],
    ),
    "ttkatugvbk": Sprite(
        pixels=[
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        ],
        name="ttkatugvbk",
        visible=True,
        collidable=True,
    ),
    "uihgaxtzkm": Sprite(
        pixels=[
            [8, 8, 8, 8, 8, 8, 8],
        ],
        name="uihgaxtzkm",
        visible=True,
        collidable=True,
        tags=["ksmzdcblcz"],
    ),
    "untfxhpddv": Sprite(
        pixels=[
            [8, 8, 8],
        ],
        name="untfxhpddv",
        visible=True,
        collidable=True,
        tags=["ksmzdcblcz", "sys_click"],
    ),
    "uzunfxpwmd": Sprite(
        pixels=[
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        ],
        name="uzunfxpwmd",
        visible=True,
        collidable=True,
        tags=["uzunfxpwmd"],
    ),
    "uzvelihpxo": Sprite(
        pixels=[
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        ],
        name="uzvelihpxo",
        visible=True,
        collidable=True,
    ),
    "vkwijvqdla": Sprite(
        pixels=[
            [-1, 15],
            [15, 15],
        ],
        name="vkwijvqdla",
        visible=True,
        collidable=True,
        tags=["hfjpeygkxy", "sys_click"],
    ),
    "xsrqllccpx": Sprite(
        pixels=[
            [11, -1, 11],
            [11, 11, 11],
        ],
        name="xsrqllccpx",
        visible=True,
        collidable=True,
        tags=["xsrqllccpx"],
    ),
    "zgsbadjnjn": Sprite(
        pixels=[
            [8, 8, 4, 8, 8],
        ],
        name="zgsbadjnjn",
        visible=True,
        collidable=True,
        tags=["ksmzdcblcz", "syaipsfndp", "sys_click"],
    ),
}
levels = [
    # Level 1
    Level(
        sprites=[
            sprites["jgfvrvnkaz"].clone().set_position(3, 4),
            sprites["nkrtlkykwe"].clone().set_position(9, 1),
            sprites["syaipsfndp"].clone().set_position(9, 0),
            sprites["uzunfxpwmd"].clone().set_position(0, 15),
            sprites["uzvelihpxo"].clone().set_position(-1, -1),
            sprites["xsrqllccpx"].clone().set_position(4, 13),
            sprites["xsrqllccpx"].clone().set_position(10, 13),
        ],
        grid_size=(16, 16),
        data={
            "steps": 30,
            "rotation": 0,
        },
    ),
    # Level 2
    Level(
        sprites=[
            sprites["jgfvrvnkaz"].clone().set_position(6, 6),
            sprites["nkrtlkykwe"].clone().set_position(5, 1),
            sprites["syaipsfndp"].clone().set_position(5, 0),
            sprites["untfxhpddv"].clone().set_position(6, 9),
            sprites["untfxhpddv"].clone().set_position(11, 11),
            sprites["uzunfxpwmd"].clone().set_position(0, 15),
            sprites["uzvelihpxo"].clone().set_position(-1, -1),
            sprites["xsrqllccpx"].clone().set_position(2, 13),
            sprites["xsrqllccpx"].clone().set_position(6, 13),
            sprites["xsrqllccpx"].clone().set_position(10, 13),
        ],
        grid_size=(16, 16),
        data={
            "steps": 45,
            "rotation": 180,
        },
    ),
    # Level 3
    Level(
        sprites=[
            sprites["jgfvrvnkaz"].clone().set_position(1, 8),
            sprites["nkrtlkykwe"].clone().set_position(1, 1),
            sprites["nkrtlkykwe"].clone().set_position(14, 1),
            sprites["nkrtlkykwe"].clone().set_position(6, 1),
            sprites["odioorqnkn"].clone().set_position(8, 7),
            sprites["odioorqnkn"].clone().set_position(1, 5),
            sprites["syaipsfndp"].clone().set_position(1, 0),
            sprites["syaipsfndp"].clone().set_position(14, 0),
            sprites["syaipsfndp"].clone().set_position(6, 0),
            sprites["trurgcakbj"].clone().set_position(10, 10),
            sprites["uzunfxpwmd"].clone().set_position(0, 15),
            sprites["uzvelihpxo"].clone().set_position(-1, -1),
            sprites["xsrqllccpx"].clone().set_position(1, 13),
            sprites["xsrqllccpx"].clone().set_position(12, 13),
            sprites["xsrqllccpx"].clone().set_position(7, 13),
        ],
        grid_size=(16, 16),
        data={
            "steps": 100,
            "rotation": 180,
        },
    ),
    # Level 4
    Level(
        sprites=[
            sprites["adbrqflmwi"].clone().set_position(2, 9),
            sprites["jgfvrvnkaz"].clone().set_position(12, 5),
            sprites["jgfvrvnkaz"].clone().set_position(5, 5),
            sprites["nkrtlkykwe"].clone().set_position(7, 1),
            sprites["syaipsfndp"].clone().set_position(7, 0),
            sprites["trurgcakbj"].clone().set_position(12, 13),
            sprites["trurgcakbj"].clone().set_position(14, 10),
            sprites["ttkatugvbk"].clone().set_position(-1, -1),
            sprites["uzunfxpwmd"].clone().set_position(0, 19),
            sprites["xsrqllccpx"].clone().set_position(2, 17),
            sprites["xsrqllccpx"].clone().set_position(16, 17),
            sprites["xsrqllccpx"].clone().set_position(8, 17),
            sprites["xsrqllccpx"].clone().set_position(12, 17),
        ],
        grid_size=(20, 20),
        data={
            "steps": 120,
            "rotation": 0,
        },
    ),
    # Level 5
    Level(
        sprites=[
            sprites["jgfvrvnkaz"].clone().set_position(2, 9),
            sprites["nkrtlkykwe"].clone().set_position(5, 1),
            sprites["nkrtlkykwe"].clone().set_position(13, 1),
            sprites["qwsmjdrvqj"].clone().set_position(8, 5),
            sprites["syaipsfndp"].clone().set_position(5, 0),
            sprites["syaipsfndp"].clone().set_position(13, 0),
            sprites["trurgcakbj"].clone().set_position(7, 13),
            sprites["ttkatugvbk"].clone().set_position(-1, -1),
            sprites["untfxhpddv"].clone().set_position(11, 9),
            sprites["uzunfxpwmd"].clone().set_position(0, 19),
            sprites["uzunfxpwmd"].clone().set_position(19, 0).set_rotation(90),
            sprites["uzunfxpwmd"].clone().set_position(-1, 0).set_rotation(90),
            sprites["xsrqllccpx"].clone().set_position(17, 6).set_rotation(270),
            sprites["xsrqllccpx"].clone().set_position(2, 17),
            sprites["xsrqllccpx"].clone().set_position(6, 17),
            sprites["xsrqllccpx"].clone().set_position(12, 17),
        ],
        grid_size=(20, 20),
        data={
            "steps": 100,
            "rotation": 180,
        },
    ),
    # Level 6
    Level(
        sprites=[
            sprites["mdhkebfsmg"].clone().set_position(14, 4),
            sprites["nkrtlkykwe"].clone().set_position(9, 1),
            sprites["qwsmjdrvqj"].clone().set_position(9, 5),
            sprites["syaipsfndp"].clone().set_position(9, 0),
            sprites["ttkatugvbk"].clone().set_position(-1, -1),
            sprites["uzunfxpwmd"].clone().set_position(0, 19),
            sprites["uzunfxpwmd"].clone().set_position(19, 0).set_rotation(90),
            sprites["uzunfxpwmd"].clone().set_rotation(90),
            sprites["vkwijvqdla"].clone().set_position(9, 14),
            sprites["xsrqllccpx"].clone().set_position(17, 9).set_rotation(270),
            sprites["xsrqllccpx"].clone().set_position(8, 17),
            sprites["xsrqllccpx"].clone().set_position(1, 11).set_rotation(90),
            sprites["xsrqllccpx"].clone().set_position(1, 6).set_rotation(90),
            sprites["zgsbadjnjn"].clone().set_position(7, 10),
        ],
        grid_size=(20, 20),
        data={
            "steps": 120,
            "rotation": 0,
        },
    ),
]
BACKGROUND_COLOR = 12
PADDING_COLOR = 1


class gxetqmbwgi(RenderableUserDisplay):
    """."""

    def __init__(self, pxfqncpydm: int = 0):
        self.pxfqncpydm = pxfqncpydm
        self.current_steps = pxfqncpydm
        super().__init__()

    def mmboppqpvb(self, fagavvtwpi: int) -> None:
        self.current_steps = max(0, min(fagavvtwpi, self.pxfqncpydm))

    def render_interface(self, frame: np.ndarray) -> np.ndarray:
        if self.pxfqncpydm == 0:
            return frame
        bmzfzpbuit = self.current_steps / self.pxfqncpydm
        imathbgwdx = round(64 * bmzfzpbuit)
        for x in range(64):
            if x < imathbgwdx:
                frame[0, x] = 14
            else:
                frame[0, x] = 0
        return frame


class hbwuwfezbg(RenderableUserDisplay):
    """."""

    def __init__(self, rotation: int = 0):
        self._k = rotation // 90 % 4

    def set_rotation(self, rotation: int) -> None:
        self._k = rotation // 90 % 4

    def render_interface(self, frame: np.ndarray) -> np.ndarray:
        if self._k == 0:
            return frame
        return np.rot90(frame, k=self._k).copy()


class Sp80(ARCBaseGame):
    """."""

    wdxitozphu = {
        1: {
            GameAction.ACTION1: GameAction.ACTION4,
            GameAction.ACTION2: GameAction.ACTION3,
            GameAction.ACTION3: GameAction.ACTION1,
            GameAction.ACTION4: GameAction.ACTION2,
        },
        2: {
            GameAction.ACTION1: GameAction.ACTION2,
            GameAction.ACTION2: GameAction.ACTION1,
            GameAction.ACTION3: GameAction.ACTION4,
            GameAction.ACTION4: GameAction.ACTION3,
        },
        3: {
            GameAction.ACTION1: GameAction.ACTION3,
            GameAction.ACTION2: GameAction.ACTION4,
            GameAction.ACTION3: GameAction.ACTION2,
            GameAction.ACTION4: GameAction.ACTION1,
        },
    }
    qxlcnqsvsf = {
        1: {
            GameAction.ACTION1: GameAction.ACTION3,
            GameAction.ACTION2: GameAction.ACTION4,
            GameAction.ACTION3: GameAction.ACTION2,
            GameAction.ACTION4: GameAction.ACTION1,
        },
        2: {
            GameAction.ACTION1: GameAction.ACTION2,
            GameAction.ACTION2: GameAction.ACTION1,
            GameAction.ACTION3: GameAction.ACTION4,
            GameAction.ACTION4: GameAction.ACTION3,
        },
        3: {
            GameAction.ACTION1: GameAction.ACTION4,
            GameAction.ACTION2: GameAction.ACTION3,
            GameAction.ACTION3: GameAction.ACTION1,
            GameAction.ACTION4: GameAction.ACTION2,
        },
    }
    mlgebkvsmt: str
    dpkgglmdup: Optional[Sprite]
    pksbqruoge: List[Tuple[Sprite, int, int]]
    shpilcvwbs: List[Sprite]
    enlvswjeov: bool
    epilwznfbr: bool
    srwrqoodsc: Set[Sprite]
    szbmtoxgbd: Set[Sprite]
    jmbhqnxkkc: int
    jvjkymhjfc: gxetqmbwgi
    awpmaspsfp: bool

    def __init__(self) -> None:
        self.mlgebkvsmt = "change"
        self.dpkgglmdup = None
        self.pksbqruoge = []
        self.shpilcvwbs = []
        self.enlvswjeov = False
        self.epilwznfbr = False
        self.srwrqoodsc = set()
        self.szbmtoxgbd = set()
        self.jmbhqnxkkc = 0
        self.jvjkymhjfc = gxetqmbwgi(pxfqncpydm=0)
        self.awpmaspsfp = False
        self.hypjnwsut = False
        self.tunzhnhfa = 0
        self.zzocrmvox = 0
        self.sywpxxgfq = 0
        self.nmcpyttlk = hbwuwfezbg(0)
        camera = Camera(
            background=BACKGROUND_COLOR,
            letter_box=PADDING_COLOR,
            interfaces=[self.jvjkymhjfc, self.nmcpyttlk],
        )
        super().__init__(
            game_id="sp80",
            levels=levels,
            camera=camera,
            available_actions=[1, 2, 3, 4, 5, 6],
        )

    def on_set_level(self, level: Level) -> None:
        self.mlgebkvsmt = "change"
        self.dpkgglmdup = None
        self.pksbqruoge = []
        self.shpilcvwbs = []
        self.enlvswjeov = False
        self.epilwznfbr = False
        self.srwrqoodsc = set()
        self.szbmtoxgbd = set()
        self.awpmaspsfp = False
        self.hypjnwsut = False
        self.zzocrmvox = 0
        for hnakeekms in level.get_sprites_by_tag("ksmzdcblcz"):
            hnakeekms.pixels[(hnakeekms.pixels >= 0) & (hnakeekms.pixels != 4)] = 8
        for hnakeekms in level.get_sprites():
            if hnakeekms.name == "xsrqllccpx":
                hnakeekms.pixels[hnakeekms.pixels >= 0] = 11
        for hnakeekms in level.get_sprites_by_tag("uzunfxpwmd"):
            hnakeekms.pixels[hnakeekms.pixels >= 0] = 1
        fagavvtwpi = level.get_data("steps") or 50
        self.tunzhnhfa = fagavvtwpi
        self.jvjkymhjfc.pxfqncpydm = fagavvtwpi
        self.jvjkymhjfc.mmboppqpvb(fagavvtwpi)
        qmctwztjyb = self.ckahxkcgfi()
        if qmctwztjyb:
            self.gchfqtwjap(qmctwztjyb)
        jngubtbiz = level.get_data("rotation") or 0
        self.sywpxxgfq = jngubtbiz // 90 % 4
        self.nmcpyttlk.set_rotation(jngubtbiz)

    def rxjmwfcjyw(self) -> List[Sprite]:
        return [s for s in self.current_level.get_sprites_by_tag("ksmzdcblcz")] + [s for s in self.current_level.get_sprites_by_tag("hfjpeygkxy")]

    def mdtzyuabwe(self) -> List[Sprite]:
        return [s for s in self.current_level.get_sprites_by_tag("nkrtlkykwe")]

    def mldlhgjtqi(self) -> List[Sprite]:
        return [s for s in self.current_level.get_sprites_by_tag("xsrqllccpx")]

    def cycphutjqn(self) -> List[Sprite]:
        return [s for s in self.current_level.get_sprites_by_tag("uzunfxpwmd")]

    def ckahxkcgfi(self) -> Optional[Sprite]:
        zurqbcwssv = self.rxjmwfcjyw()
        if not zurqbcwssv:
            return None
        return min(zurqbcwssv, key=lambda futcsxmviu: futcsxmviu.x**2 + futcsxmviu.y**2)

    def aqltiyljgy(self, rpilpsmmjr: Sprite, x: int, y: int) -> bool:
        """."""
        lybdljomvc = rpilpsmmjr.width
        trvtwyuduw = rpilpsmmjr.height
        if y < 3:
            return False
        for rxocuufmgq in self.mldlhgjtqi():
            rx, ry = (rxocuufmgq.x, rxocuufmgq.y)
            ajqdzrqbmm = rxocuufmgq.width
            veahmazqui = rxocuufmgq.height
            if x < rx + ajqdzrqbmm + 1 and x + lybdljomvc > rx - 1 and (y < ry + veahmazqui + 1) and (y + trvtwyuduw > ry - 1):
                return False
        return True

    def ccgagqcmlv(self, ralthebbsm: Sprite, ehobpbwgqv: Sprite) -> bool:
        ax1, ay1, ax2, ay2 = (
            ralthebbsm.x,
            ralthebbsm.y,
            ralthebbsm.x + ralthebbsm.width,
            ralthebbsm.y + ralthebbsm.height,
        )
        bx1, by1, bx2, by2 = (
            ehobpbwgqv.x,
            ehobpbwgqv.y,
            ehobpbwgqv.x + ehobpbwgqv.width,
            ehobpbwgqv.y + ehobpbwgqv.height,
        )
        return ax1 < bx2 and ax2 > bx1 and (ay1 < by2) and (ay2 > by1)

    def gchfqtwjap(self, rpilpsmmjr: Sprite) -> None:
        if self.dpkgglmdup is not None:
            self.dgtqqipvxj()
        self.dpkgglmdup = rpilpsmmjr
        if rpilpsmmjr is not None:
            rpilpsmmjr.pixels[(rpilpsmmjr.pixels >= 0) & (rpilpsmmjr.pixels != 4)] = 9
            rpilpsmmjr.set_layer(1)
        self.awpmaspsfp = True

    def dgtqqipvxj(self) -> None:
        if self.dpkgglmdup is not None:
            fxxuvnwtvi = 15 if "hfjpeygkxy" in self.dpkgglmdup.tags else 8
            self.dpkgglmdup.pixels[(self.dpkgglmdup.pixels >= 0) & (self.dpkgglmdup.pixels != 4)] = fxxuvnwtvi
            self.dpkgglmdup.set_layer(0)
        self.dpkgglmdup = None

    def tadqvfdobr(self) -> None:
        self.mlgebkvsmt = "spill"
        self.dgtqqipvxj()
        self.pksbqruoge = [(coalstikmk, 0, 1) for coalstikmk in self.mdtzyuabwe()]
        self.shpilcvwbs = []
        self.enlvswjeov = False
        self.epilwznfbr = False
        self.srwrqoodsc = set()
        self.szbmtoxgbd = set()
        for mgqvpwjovi in self.current_level.get_sprites_by_tag("syaipsfndp"):
            px, py = (mgqvpwjovi.x, mgqvpwjovi.y)
            arr = mgqvpwjovi.pixels
            for y in range(arr.shape[0]):
                for x in range(arr.shape[1]):
                    if int(arr[y, x]) == 4:
                        dwpbeschlm, irfmxaorsf = (px + x, py + y)
                        tcrfiyjopc = self.current_level.get_sprite_at(dwpbeschlm, irfmxaorsf + 1)
                        ubhgljcvxu = tcrfiyjopc and "nkrtlkykwe" in getattr(tcrfiyjopc, "tags", [])
                        if not ubhgljcvxu and self.current_level.get_sprite_at(dwpbeschlm, irfmxaorsf + 1) is None:
                            ackqyairgy = sprites["nkrtlkykwe"].clone().set_position(dwpbeschlm, irfmxaorsf + 1)
                            self.current_level.add_sprite(ackqyairgy)
                            self.pksbqruoge.append((ackqyairgy, 0, 1))
                            self.shpilcvwbs.append(ackqyairgy)

    def yxidiymutj(self) -> None:
        for s in self.shpilcvwbs:
            self.current_level.remove_sprite(s)
        self.shpilcvwbs = []
        for s in self.mldlhgjtqi():
            s.pixels[s.pixels >= 0] = 11
        for s in self.cycphutjqn():
            s.pixels[s.pixels >= 0] = 1
        self.srwrqoodsc = set()
        self.szbmtoxgbd = set()
        self.mlgebkvsmt = "change"
        self.enlvswjeov = False
        self.epilwznfbr = False
        self.pksbqruoge = []
        self.zzocrmvox += 1
        qmctwztjyb = self.ckahxkcgfi()
        if qmctwztjyb:
            self.gchfqtwjap(qmctwztjyb)

    def step(self) -> None:
        axxkvkila, kmqfjqint = self.lnqtlqefzv()
        if self.mlgebkvsmt == "change":
            if axxkvkila != GameAction.RESET:
                self.rpnnowtzay(1)
            if axxkvkila == GameAction.ACTION6:
                ndacyzjzp = kmqfjqint.get("x", 0)
                cuovqxuvp = kmqfjqint.get("y", 0)
                wjotjhfpqt = self.camera.display_to_grid(ndacyzjzp, cuovqxuvp)
                if wjotjhfpqt:
                    dwpbeschlm, irfmxaorsf = wjotjhfpqt
                    pmghxbqvjk: Optional[Sprite] = None
                    for futcsxmviu in self.rxjmwfcjyw():
                        if futcsxmviu.x <= dwpbeschlm < futcsxmviu.x + futcsxmviu.width and futcsxmviu.y <= irfmxaorsf < futcsxmviu.y + futcsxmviu.height:
                            pmghxbqvjk = futcsxmviu
                            break
                    if pmghxbqvjk:
                        self.gchfqtwjap(pmghxbqvjk)
                        self.hypjnwsut = True
                        self.complete_action()
                        return
            if self.dpkgglmdup is not None:
                worqgwkuyx, patlrtoom = (0, 0)
                if axxkvkila == GameAction.ACTION1:
                    patlrtoom = -1
                elif axxkvkila == GameAction.ACTION2:
                    patlrtoom = 1
                elif axxkvkila == GameAction.ACTION3:
                    worqgwkuyx = -1
                elif axxkvkila == GameAction.ACTION4:
                    worqgwkuyx = 1
                if worqgwkuyx != 0 or patlrtoom != 0:
                    pceslewgef = self.dpkgglmdup.x + worqgwkuyx
                    mcpssfghmx = self.dpkgglmdup.y + patlrtoom
                    if self.aqltiyljgy(self.dpkgglmdup, pceslewgef, mcpssfghmx):
                        collisions = self.try_move_sprite(self.dpkgglmdup, worqgwkuyx, patlrtoom)
                        if len(collisions) > 0 and all(["ksmzdcblcz" in c.tags or "hfjpeygkxy" in c.tags for c in collisions]):
                            self.dpkgglmdup.move(worqgwkuyx, patlrtoom)
                    self.hypjnwsut = False
                    self.complete_action()
                    self.awpmaspsfp = False
                    return
            if axxkvkila == GameAction.ACTION5:
                if self.zzocrmvox >= 4:
                    self.lose()
                    self.complete_action()
                    return
                self.tadqvfdobr()
                self.awpmaspsfp = False
                self.hypjnwsut = False
                return
            self.complete_action()
            return
        elif self.mlgebkvsmt == "spill":
            if self.epilwznfbr:
                dojowtxhlx = self.mldlhgjtqi()
                inszeuniyy = all((r in self.srwrqoodsc for r in dojowtxhlx))
                if self.enlvswjeov or not inszeuniyy:
                    if self.jmbhqnxkkc < 6:
                        for ymuguhctww in self.szbmtoxgbd:
                            ymuguhctww.pixels[ymuguhctww.pixels >= 0] = 14 if self.jmbhqnxkkc % 2 == 1 else 1
                        if self.jmbhqnxkkc < 5:
                            for rxocuufmgq in self.mldlhgjtqi():
                                if rxocuufmgq not in self.srwrqoodsc:
                                    rxocuufmgq.pixels[rxocuufmgq.pixels >= 0] = 0 if self.jmbhqnxkkc % 2 == 0 else 11
                        self.jmbhqnxkkc += 1
                    else:
                        self.yxidiymutj()
                        if self.tunzhnhfa <= 0:
                            self.lose()
                        self.complete_action()
                else:
                    self.complete_action()
                    self.next_level()
                return
            mapivzldnw: List[Tuple[Sprite, int, int]] = []
            for coalstikmk, worqgwkuyx, patlrtoom in self.pksbqruoge:
                mvswvwdul, ggdytkpvw = (coalstikmk.x, coalstikmk.y)
                adjx1, adjx2 = (-1, 1) if patlrtoom != 0 else (0, 0)
                adjy1, adjy2 = (-1, 1) if patlrtoom == 0 else (0, 0)
                slczixltov = [(adjx1, adjy1), (adjx2, adjy2)]
                tcrfiyjopc = self.current_level.get_sprite_at(mvswvwdul + worqgwkuyx, ggdytkpvw + patlrtoom)
                if tcrfiyjopc is None:
                    ackqyairgy = sprites["nkrtlkykwe"].clone().set_position(mvswvwdul + worqgwkuyx, ggdytkpvw + patlrtoom)
                    self.current_level.add_sprite(ackqyairgy)
                    mapivzldnw.append((ackqyairgy, worqgwkuyx, patlrtoom))
                    self.shpilcvwbs.append(ackqyairgy)
                    continue
                if "nkrtlkykwe" in tcrfiyjopc.tags:
                    mapivzldnw.append((tcrfiyjopc, worqgwkuyx, patlrtoom))
                if "ksmzdcblcz" in tcrfiyjopc.tags:
                    for eisjmhtvre, acsawzwkti in slczixltov:
                        if self.current_level.get_sprite_at(mvswvwdul + eisjmhtvre, ggdytkpvw + acsawzwkti) is None:
                            ackqyairgy = sprites["nkrtlkykwe"].clone().set_position(mvswvwdul + eisjmhtvre, ggdytkpvw + acsawzwkti)
                            self.current_level.add_sprite(ackqyairgy)
                            mapivzldnw.append((ackqyairgy, worqgwkuyx, patlrtoom))
                            self.shpilcvwbs.append(ackqyairgy)
                    continue
                if "xsrqllccpx" in tcrfiyjopc.tags:
                    tfilpikkqk = self.current_level.get_sprite_at(mvswvwdul + adjx1, ggdytkpvw + adjy1)
                    lkppwwuqyh = self.current_level.get_sprite_at(mvswvwdul + adjx2, ggdytkpvw + adjy2)
                    if tfilpikkqk is tcrfiyjopc and lkppwwuqyh is tcrfiyjopc:
                        tcrfiyjopc.pixels[tcrfiyjopc.pixels >= 0] = 13
                        self.srwrqoodsc.add(tcrfiyjopc)
                        continue
                    else:
                        for eisjmhtvre, acsawzwkti in slczixltov:
                            if self.current_level.get_sprite_at(mvswvwdul + eisjmhtvre, ggdytkpvw + acsawzwkti) is None:
                                ackqyairgy = sprites["nkrtlkykwe"].clone().set_position(mvswvwdul + eisjmhtvre, ggdytkpvw + acsawzwkti)
                                self.current_level.add_sprite(ackqyairgy)
                                mapivzldnw.append((ackqyairgy, worqgwkuyx, patlrtoom))
                                self.shpilcvwbs.append(ackqyairgy)
                        continue
                if "hfjpeygkxy" in tcrfiyjopc.tags:
                    tfilpikkqk = self.current_level.get_sprite_at(mvswvwdul + adjx1, ggdytkpvw + adjy1)
                    lkppwwuqyh = self.current_level.get_sprite_at(mvswvwdul + adjx2, ggdytkpvw + adjy2)
                    if tfilpikkqk is tcrfiyjopc and lkppwwuqyh is None:
                        chvgmceunz = patlrtoom
                        zazslqutzx = -worqgwkuyx
                        ackqyairgy = sprites["nkrtlkykwe"].clone().set_position(mvswvwdul + chvgmceunz, ggdytkpvw + zazslqutzx)
                        self.current_level.add_sprite(ackqyairgy)
                        mapivzldnw.append((ackqyairgy, chvgmceunz, zazslqutzx))
                        self.shpilcvwbs.append(ackqyairgy)
                    if lkppwwuqyh is tcrfiyjopc and tfilpikkqk is None:
                        chvgmceunz = -patlrtoom
                        zazslqutzx = worqgwkuyx
                        ackqyairgy = sprites["nkrtlkykwe"].clone().set_position(mvswvwdul + chvgmceunz, ggdytkpvw + zazslqutzx)
                        self.current_level.add_sprite(ackqyairgy)
                        mapivzldnw.append((ackqyairgy, chvgmceunz, zazslqutzx))
                        self.shpilcvwbs.append(ackqyairgy)
                    else:
                        for eisjmhtvre, acsawzwkti in slczixltov:
                            if self.current_level.get_sprite_at(mvswvwdul + eisjmhtvre, ggdytkpvw + acsawzwkti) is None:
                                ackqyairgy = sprites["nkrtlkykwe"].clone().set_position(mvswvwdul + eisjmhtvre, ggdytkpvw + acsawzwkti)
                                self.current_level.add_sprite(ackqyairgy)
                                mapivzldnw.append((ackqyairgy, worqgwkuyx, patlrtoom))
                                self.shpilcvwbs.append(ackqyairgy)
                        continue
                if "uzunfxpwmd" in tcrfiyjopc.tags:
                    tcrfiyjopc.pixels[tcrfiyjopc.pixels >= 0] = 14
                    self.szbmtoxgbd.add(tcrfiyjopc)
                    self.enlvswjeov = True
                    continue
            self.pksbqruoge = mapivzldnw
            if not self.pksbqruoge:
                self.epilwznfbr = True
                self.jmbhqnxkkc = 0
            return

    def udeubouzyp(self, olvhpcnbsh: int, mviqpduaav: int) -> Tuple[int, int]:
        """."""
        k = self.sywpxxgfq
        if k == 0:
            return (olvhpcnbsh, mviqpduaav)
        if k == 1:
            return (63 - mviqpduaav, olvhpcnbsh)
        if k == 2:
            return (63 - olvhpcnbsh, 63 - mviqpduaav)
        return (mviqpduaav, 63 - olvhpcnbsh)

    def fewyrfijcb(self, dwpbeschlm: int, irfmxaorsf: int) -> Tuple[int, int]:
        """."""
        k = self.sywpxxgfq
        if k == 0:
            return (dwpbeschlm, irfmxaorsf)
        if k == 1:
            return (irfmxaorsf, 63 - dwpbeschlm)
        if k == 2:
            return (63 - dwpbeschlm, 63 - irfmxaorsf)
        return (63 - irfmxaorsf, dwpbeschlm)

    def lnqtlqefzv(self) -> Tuple[GameAction, Dict[str, Any]]:
        """."""
        k = self.sywpxxgfq
        ehmbtpreks = self.action.id
        data = self.action.data
        if k == 0:
            return (ehmbtpreks, data)
        if ehmbtpreks in self.wdxitozphu.get(k, {}):
            return (self.wdxitozphu[k][ehmbtpreks], data)
        if ehmbtpreks == GameAction.ACTION6:
            olvhpcnbsh = data.get("x", 0)
            mviqpduaav = data.get("y", 0)
            dwpbeschlm, irfmxaorsf = self.udeubouzyp(olvhpcnbsh, mviqpduaav)
            return (ehmbtpreks, {"x": dwpbeschlm, "y": irfmxaorsf})
        return (ehmbtpreks, data)

    def rpnnowtzay(self, znmndtybio: int) -> None:
        """."""
        self.tunzhnhfa = max(0, self.tunzhnhfa - znmndtybio)
        self.jvjkymhjfc.mmboppqpvb(self.tunzhnhfa)
        if self.tunzhnhfa <= 0:
            self.lose()
            self.complete_action()
            return
