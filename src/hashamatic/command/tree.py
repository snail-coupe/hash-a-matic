"""fractal tree generation"""

import logging
import math
import random
from argparse import Namespace

from PIL import ImageDraw
from PIL.Image import Image
from PIL.Image import new as NewImage

try:
    from hashamatic.command import BotCmd, BotResult, iRandom

    class Tree(BotCmd, iRandom):
        """A fractal tree."""

        tags: list[str] = ["tree", "🌳", "ProcGen", "art", "botArt"]
        caption = "Look at this tree I grew. 🌳"

        def run(self, _args: Namespace) -> BotResult:
            return BotResult(
                FractalTree().render(),
                text=self.caption,
                tags=self.tags,
                alt_text="A computer generated fractal tree",
            )

except ImportError:
    logging.debug("failed to import BotCmd interface")


class FractalTree:
    """class to generate fractal trees"""

    def __init__(self):
        self.w = self.h = 1024
        self.r = 10
        self.spread = 30
        self.lr = (-5, 3)
        self.la = (-5, 5)
        self.leaves: set[tuple[float, float]] = set()  # type: ignore

    def branch(
        self,
        draw: ImageDraw.ImageDraw,
        angle: float,
        base: tuple[float, float],
        length: float,
        depth: int = 1,
    ):
        """branch a trunk"""

        e = (
            length * math.sin(math.radians(angle)),
            length * math.cos(math.radians(angle)),
        )
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
        """render the tree to a PIL.Image"""
        img = NewImage("RGB", (self.w, self.h))
        draw = ImageDraw.Draw(img)

        angle = -180
        base = (self.w / 2, self.h * 9 / 10)
        length = 100

        self.leaves.clear()
        self.branch(draw, angle, base, length)
        for point in self.leaves:
            green: int = int(random.uniform(128, 224))
            draw.regular_polygon(
                (*point, random.uniform(3, 6)), n_sides=7, fill=f"rgb(0, {green}, 0)"
            )
        return img


if __name__ == "__main__":
    t = FractalTree()
    i = t.render()
    i.save("temp.png", "PNG")
