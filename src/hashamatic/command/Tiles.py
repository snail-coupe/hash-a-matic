''' defines various TileRenderers for use by other modules '''
from __future__ import annotations

import random

from typing import Dict, List, Tuple

from PIL import ImageDraw
from PIL.Image import Image
from PIL.Image import new as NewImage


class TileRenderer():
    ''' This base class specifies the interface for generating and rendering Tile '''

    renderers: Dict[str, TileRenderer] = {}  # cls variable

    def __init_subclass__(cls, /, **kwargs):
        super().__init_subclass__(**kwargs)
        if not cls.__name__.startswith("_"):
            cls.renderers[cls.__name__] = cls()

    def render(self, width: int, border: int) -> Image:
        ''' return a width x width image '''
        raise NotImplementedError

    @classmethod
    def get_choices(cls) -> List[str]:
        ''' return list of registed renderers '''
        return list(cls.renderers)
    
    @classmethod
    def get_default(cls) -> str:
        ''' return a default renderer '''
        if "PlainTile" in cls.renderers:
            return "PlainTile"
        return list(cls.renderers.keys())[0]


class PlainTile(TileRenderer):
    ''' a plain tile of a random colour '''

    def render(self, width: int, border: int) -> Image:
        ret = NewImage("RGB", (width, width))
        draw = ImageDraw.Draw(ret)
        (r, g, b) = [random.choice(range(256)) for x in range(3)]
        draw.rectangle((
            (border, border),
            (width-border, width-border)
        ), f"rgb({r},{g},{b})")

        return ret


class SpaceInvader(TileRenderer):
    ''' renders a spae invader '''

    def generate_invader(self, colours: int = 2) -> Dict[Tuple[int, int], int]:
        ''' generate a single 6x6 alien '''

        ret: Dict[Tuple[int, int], int] = dict()

        for r in range(6):
            for c in range(3):
                colour = random.choice(range(colours))
                ret[(r, c)] = colour
                ret[(r, 5-c)] = colour

        return ret

    def render(self, width: int, border: int) -> Image:
        colours = [
            (0, 0, 0),
            (random.choice(range(256)), random.choice(range(256)), random.choice(range(256))),
            (random.choice(range(256)), random.choice(range(256)), random.choice(range(256))),
            (random.choice(range(256)), random.choice(range(256)), random.choice(range(256))),
        ]
        px = int(width/8)
        ret = NewImage("RGB", (width, width))
        draw = ImageDraw.Draw(ret)
        alien = self.generate_invader(3)
        for (r, c), value in alien.items():
            draw.rectangle((
                (border+(c+1)*px, border+(r+1)*px),
                (border+(c+2)*px, border+(r+2)*px)
            ), f"rgb{colours[value]}")
        return ret
