''' attempt to make some sort of caverns '''

from __future__ import annotations

import collections
import logging
import random
from argparse import ArgumentParser, Namespace
from typing import Dict, List, Tuple, Optional

from PIL import ImageDraw
from PIL.Image import Image
from PIL.Image import new as NewImage

try:
    from hashamatic.command import BotCmd, BotResult, iRandom

    class Caves(BotCmd, iRandom):
        ''' a bad implmentation of a fractal map '''

        tags: List[str] = ["art", "botArt"]

        @staticmethod
        def add_argparse_arguments(parser: ArgumentParser) -> ArgumentParser:
            return parser

        def run(self, _args: Namespace) -> BotResult:
            # imageRaw = fractalCaves(256).generate().render()
            t = FractalCaves(64, iterations=2).generate().double()
            t.smooth(1).double().smooth(1).double().smooth(4)
            image_raw = t.render()
            return BotResult(
                image_raw, tags=self.tags,
                alt_text="A computer generated fractal map using the 5:4 algorithm."
            )

except ImportError:
    logging.debug("failed to import BotCmd interface")


class FractalCaves():
    ''' a bad implmentation of a fractal map using 5:4 '''

    def __init__(self, x: int = 64, y: Optional[int] = None, iterations=5):
        self.x = x
        if y:
            self.y = y
        else:
            self.y = x
        self.iterations = iterations
        self.land: Dict[Tuple[int, int], bool] = collections.defaultdict(bool)

    def reset(self):
        ''' reset the land '''
        self.land = collections.defaultdict(bool)
        for x in range(self.x):
            for y in range(self.y):
                self.land[(x, y)] = random.random() > 0.55

    def double(self) -> FractalCaves:
        ''' double the resolution '''
        new_land = collections.defaultdict(bool)
        self.x = self.x * 2
        self.y = self.y * 2
        for x in range(0, self.x, 2):
            for y in range(0, self.y, 2):
                v = self.land[(int(x / 2), int(y / 2))]
                new_land[(x, y)] = v
                new_land[(x + 1, y)] = v
                new_land[(x, y + 1)] = v
                new_land[(x + 1, y + 1)] = v
        self.land = new_land
        return self

    def normed(self, x, y):
        ''' normalise a point based upon the surrounding points '''
        pc = 0
        for xo in range(x - 1, x + 2):
            xx = xo % self.x
            for yo in range(y - 1, y + 2):
                yy = yo % self.y
                if self.land[(xx, yy)]:
                    pc = pc + 1
        return pc > 4

    def antialias(self, x, y):
        ''' bad antialising '''
        pc = 0
        for xo in range(x - 1, x + 2):
            xx = xo % self.x
            for yo in range(y - 1, y + 2):
                yy = yo % self.y
                if self.land[(xx, yy)]:
                    pc = pc + 1
        g = 32 * pc - 1
        b = 255 - g
        return (0, g, b)

    def smooth(self, iterations) -> FractalCaves:
        ''' smoothing '''
        for _ in range(iterations):
            new_land = collections.defaultdict(bool)
            for x in range(self.x):
                for y in range(self.y):
                    new_land[(x, y)] = self.normed(x, y)
            self.land = new_land
        return self

    def generate(self) -> FractalCaves:
        ''' basic generation '''
        self.reset()
        self.smooth(self.iterations)
        return self

    def render(self) -> Image:
        ''' render to a PIL.Image '''
        img = NewImage("RGB", (
            self.x, self.y
        ))
        draw = ImageDraw.Draw(img)

        for p in self.land.keys():
            # if(self.land[p]):
            #    col=(0,255,0)
            # else:
            #    col=(0,0,255)
            # draw.point([p], col)
            draw.point([p], self.antialias(*p))

        return img


if __name__ == "__main__":
    cves = FractalCaves(32, iterations=2)
    cves.generate()
    cves.double()
    cves.smooth(1)
    cves.double()
    cves.smooth(1)
    cves.double()
    cves.smooth(4)
    i = cves.render()
    i.save("temp.png", "PNG")
