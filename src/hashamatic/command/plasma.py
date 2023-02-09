import collections
import logging
import random
from argparse import Namespace
from typing import Dict, List, Tuple

from PIL import ImageDraw
from PIL.Image import Image
from PIL.Image import new as NewImage

try:
    from hashamatic.command import BotCmd, BotResult, iRandom

    class Plasma(BotCmd, iRandom):
        ''' A randomly generated, multi-coloured, fractal plasma '''

        tags: List[str] = ["plasma", "cloud", "☁️", "fractal", "art", "botArt"]
        caption = "Look at this space cloud I made."

        def run(self, args: Namespace) -> BotResult:
            return BotResult(
                fractalMap(256).render(), text=self.caption, tags=self.tags,
                alt_text="A computer generated, multi-coloured, fractal plasma. Generated using the Diamond-Square algorithm."
            )
except ImportError:
    logging.debug("failed to import BotCmd interface")


class fractalMap():
    ''' a bad implmentation of a cloud fractal:
        https://en.wikipedia.org/wiki/Diamond-square_algorithm '''

    def __init__(self, blockSize: int = 256, xb: int = 1, yb: int = 1):
        self.blockSize = blockSize
        self.xb = xb
        self.yb = yb
        self.heights: Dict[Tuple[int, int], float] = collections.defaultdict(float)
        self.v = lambda x: random.gauss(0, x)

    def reset(self):
        self.heights = collections.defaultdict(float)

    def plusAv(self, x: int, y: int, d: int):
        if (x, y) in self.heights:
            return

        v = list()
        if (x - d, y) in self.heights:
            v.append(self.heights[(x - d, y)])
        if (x + d, y) in self.heights:
            v.append(self.heights[(x + d, y)])
        if (x, y - d) in self.heights:
            v.append(self.heights[(x, y - d)])
        if (x, y + d) in self.heights:
            v.append(self.heights[(x, y + d)])
        self.heights[(x, y)] = sum(v) / len(v) + self.v(d)

    def crossAv(self, x: int, y: int, d: int):
        if (x, y) in self.heights:
            return
        v = list()
        if (x - d, y - d) in self.heights:
            v.append(self.heights[(x - d, y - d)])
        if (x + d, y - d) in self.heights:
            v.append(self.heights[(x + d, y - d)])
        if (x - d, y + d) in self.heights:
            v.append(self.heights[(x - d, y + d)])
        if (x + d, y + d) in self.heights:
            v.append(self.heights[(x + d, y + d)])
        self.heights[(x, y)] = sum(v) / len(v) + self.v(d)

    def midFill(self, x: int, y: int, s: int):
        # A.2.A
        # .3.3.
        # 2.1.2
        # .3.3.
        # A.2.A

        m = int(s / 2)
        # now fill in 2
        self.plusAv(x + m, y, m)
        self.plusAv(x, y + m, m)
        self.plusAv(x + m, y + s, m)
        self.plusAv(x + s, y + m, m)

        if m > 1:
            n = int(m / 2)

            # now fill in 3
            self.crossAv(x + n, y + n, n)
            self.crossAv(x + n + m, y + n, n)
            self.crossAv(x + n, y + n + m, n)
            self.crossAv(x + n + m, y + n + m, n)

            # and recurse
            self.midFill(x, y, m)
            self.midFill(x + m, y, m)
            self.midFill(x, y + m, m)
            self.midFill(x + m, y + m, m)

    def normalise(self):
        mn = mx = self.heights[(0, 0)]
        for p in self.heights.keys():
            d = self.heights[p]
            if d < mn:
                mn = d
            if d > mx:
                mx = d
        r = mx - mn
        f = 255 / r
        for p in self.heights.keys():
            self.heights[p] = (self.heights[p] - mn) * f

    def renderBlocks(self):
        s = self.blockSize
        m = int(s / 2)
        for xb in range(0, self.xb):
            x = xb * s
            for yb in range(0, self.yb):
                y = yb * s
                for corner in [(x, y), (x + s, y), (x, y + s), (x + s, y + s)]:
                    if corner not in self.heights:
                        self.heights[corner] = random.uniform(0, 256)
                if (x + m, y + m) not in self.heights:
                    self.crossAv(x + m, y + m, m)
                self.midFill(x, y, s)

    def render(self) -> Image:
        img = NewImage("RGB", (
            self.blockSize * self.xb, self.blockSize * self.yb
        ))
        draw = ImageDraw.Draw(img)

        self.reset()
        self.renderBlocks()
        self.normalise()
        red = dict(self.heights)

        self.reset()
        self.renderBlocks()
        self.normalise()
        green = dict(self.heights)

        self.reset()
        self.renderBlocks()
        self.normalise()
        blue = dict(self.heights)

        for p in self.heights.keys():
            draw.point([p], (
                int(red[p]),
                int(green[p]),
                int(blue[p])))

        return img


if __name__ == "__main__":
    t = fractalMap(128, 3, 2)
    i = t.render()
    i.save("temp.png", "PNG")
