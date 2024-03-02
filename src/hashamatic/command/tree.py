import logging
import math
import random
from argparse import Namespace
from typing import List, Set, Tuple

from PIL import ImageDraw
from PIL.Image import Image
from PIL.Image import new as NewImage

try:
    from hashamatic.command import BotCmd, BotResult, iRandom

    class Tree(BotCmd, iRandom):
        ''' A fractal tree. '''

        tags: List[str] = ["tree", "🌳", "fractal", "art", "botArt"]
        caption = "Look at this tree I grew. 🌳"

        def run(self, _args: Namespace) -> BotResult:
            return BotResult(
                fractalTree().render(), text=self.caption, tags=self.tags,
                alt_text="A computer generated fractal tree"
            )

except ImportError:
    logging.debug("failed to import BotCmd interface")


class fractalTree():

    def __init__(self):
        self.w = self.h = 1024
        self.r = 10
        self.spread = 30
        self.lr = (-5, 3)
        self.la = (-5, 5)
        self.leaves: Set[Tuple[int, int]] = set()

    def branch(self, draw, angle, base, length, depth=1):
        e = (length * math.sin(math.radians(angle)), length * math.cos(math.radians(angle)))
        f = (base[0] + e[0], base[1] + e[1])
        draw.line([base, f], fill="rgb(126, 46, 31)", width=1 + int(length / 10))
        length = length - self.r
        if length > 5:
            lp = length + random.uniform(*self.lr)
            ap = angle + self.spread + random.uniform(*self.la)
            self.branch(draw, ap, f, lp, depth + 1)
            lp = length + random.uniform(*self.lr)
            ap = angle - self.spread + random.uniform(*self.la)
            self.branch(draw, ap, f, lp, depth + 1)
            if random.randint(0, depth + 1) < 2:
                lp = length + random.uniform(*self.lr)
                ap = angle + random.uniform(*self.la)
                self.branch(draw, ap, f, lp, depth + 1)
        else:
            self.leaves.add(f)

    def render(self) -> Image:
        img = NewImage("RGB", (
            self.w, self.h
        ))
        draw = ImageDraw.Draw(img)

        angle = -180
        base = (self.w / 2, self.h * 9 / 10)
        length = 100

        self.leaves.clear()
        self.branch(draw, angle, base, length)
        for point in self.leaves:
            draw.regular_polygon(
                (*point, random.uniform(3, 6)),
                n_sides=7,
                fill="rgb(0, %d, 0)" % random.uniform(128, 224))
        return img


if __name__ == "__main__":
    t = fractalTree()
    i = t.render()
    i.save("temp.png", "PNG")
