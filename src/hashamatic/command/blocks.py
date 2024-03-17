''' Hashamatic module to generate packings of squares '''

import collections
import logging
import random
from argparse import ArgumentParser, Namespace
from typing import Dict, List

from PIL import ImageDraw
from PIL.Image import Image
from PIL.Image import new as NewImage

try:
    from hashamatic.command import BotCmd, BotResult, iRandom

    class Blocks(BotCmd, iRandom):
        ''' A packing of various sized coloured squares into a grid. '''

        tags: List[str] = ["squares", "🔲", "ProcGen", "art", "botArt"]

        @staticmethod
        def add_argparse_arguments(parser: ArgumentParser) -> ArgumentParser:
            parser.add_argument("rows", type=int, nargs='?')
            parser.add_argument("columns", type=int, nargs='?')
            return parser

        def run(self, args: Namespace) -> BotResult:
            cols = args.columns
            rows = args.rows
            if not rows:
                rows = random.randint(12, 32)
            else:
                rows = max(rows, 1)
                rows = min(rows, 65)
            if not cols:
                cols = rows
            else:
                cols = max(cols, 1)
                cols = min(cols, 65)

            b = BlocksMaker(rows, cols)
            b.generate()
            raw_image = b.render()
            return BotResult(
                raw_image, tags=self.tags,
                alt_text=f"A computer generated picture of multicoloured squares of various sizes packed into a {cols} by {rows} grid"
            )

        def random(self) -> BotResult:
            size = random.randint(12, 32)
            parser = self.add_argparse_arguments(ArgumentParser())
            args = parser.parse_args(f"{size}".split())
            return self.run(args)


except ImportError:
    logging.debug("failed to import BotCmd interface")

# first define a grid of 1x1 squares
# then iterate over each square:
#     1 in probs chance of enterig growth stage
#     if in growth stage repeat maxs-1 times:
#         if room to grow:
#             1 in probi chance of growing by 1


class BlocksMaker():
    ''' generate packings of random sized and coloured blocks '''

    map: Dict[int, Dict[int, str]] = collections.defaultdict(dict)
    maxs = 5  # max square size
    probs = 7  # 1:x chance of seed square entering growth
    probi = 2  # 1:x chance of growing each pass of growth iteration

    def __init__(
        self,
        rows: int = 10, columns: int = 10,
        block_size: int = 80,
        border_width: int = 4,
    ):
        self.rows = rows
        self.columns = columns
        self.block_size = block_size
        self.border_width = border_width

    def generate(self):
        self.map = collections.defaultdict(dict)
        for r in range(-1, 1 + self.rows):
            for c in range(-1, 1 + self.columns):
                self.map[r][c] = None
        for r in range(self.rows):
            for c in range(self.columns):
                if self.map[r][c]:
                    continue
                s = 1
                if not random.choice(range(self.probs)):
                    for _ in range(1, self.maxs):
                        if (c + s) < self.columns:
                            if (r + s) < self.rows:
                                if not self.map[r + s + 1][c]:
                                    if not self.map[r][c + s + 1]:
                                        if not random.choice(range(self.probi)):
                                            s = s + 1
                for x in range(s):
                    for y in range(s):
                        self.map[r + y][c + x] = "%d:%d:%d" % (s, r, c)
        return self

    def render(self) -> Image:
        bs = self.block_size
        bw = self.border_width
        img = NewImage("RGB", (
            bs * self.columns, bs * self.rows
        ))
        draw = ImageDraw.Draw(img)
        for r in range(self.rows):
            for c in range(self.columns):
                if ":%d:%d" % (r, c) in self.map[r][c]:
                    s = int(self.map[r][c][0])
                    draw.rectangle((
                        (c * bs + bw, r * bs + bw),
                        ((c + s) * bs - bw, (r + s) * bs - bw)
                    ), "rgb(%d,%d,%d)" % (
                        random.choice(range(256)),
                        random.choice(range(256)),
                        random.choice(range(256))
                    ))
        return img

    def renderMask(self) -> Image:
        bs = self.block_size
        bw = self.border_width
        mask = NewImage("1", (
            bs * self.columns, bs * self.rows
        ))
        draw = ImageDraw.Draw(mask)
        for r in range(self.rows):
            for c in range(self.columns):
                if ":%d:%d" % (r, c) in self.map[r][c]:
                    s = int(self.map[r][c][0])
                    draw.rectangle((
                        (c * bs + bw, r * bs + bw),
                        ((c + s) * bs - bw, (r + s) * bs - bw)
                    ), True)
        return mask
